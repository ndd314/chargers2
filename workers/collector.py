from __future__ import print_function

from config import *
import logging
import anyconfig

# TODO add logging and newrelic monitor

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

from changepoint import Charger, ChargePointConnection

import copy
import redis
import json
import time
import newrelic.agent

garage_data = anyconfig.load("garage_data.json")['garage_data']
cp = ChargePointConnection(CHARGEPOINT_USERNAME, CHARGEPOINT_PASSWORD)
r = redis.StrictRedis.from_url(REDIS_URL)

@newrelic.agent.background_task()
def get_current():
   local_garage_data = copy.deepcopy(garage_data)
   #todo there are three same calls to chargepoint.com here
   for garage_name, garage_info in local_garage_data.iteritems():
      # fix GUI crash for mission college / santa clara sites that my account don't have access to
      local_garage_data[garage_name][u'available_ports'] = 0
      logger.debug("Starting with garage {}".format(garage_name))
      for charger in cp.get_vmware_stations(regex=garage_info['regex']):
         logger.debug("Processing: {}:{}".format(garage_name,charger.sname))
         local_garage_data[garage_name]['stations'][charger.sname] = charger.port_count["available"]
         if 'available_ports' in local_garage_data[garage_name]:
            local_garage_data[garage_name][u'available_ports'] += charger.port_count["available"]
         else:
            local_garage_data[garage_name][u'available_ports'] = charger.port_count["available"]
   return local_garage_data


@newrelic.agent.background_task()
def store_to_redis(data):
   logger.info("store_to_redis(): Starting...")
   string_data = json.dumps(data)

   old_ts = r.hget("current", "timestamp")
   old_data = r.hget("current", "data")

   r.hset("current", "data", string_data)
   r.hset("current", "timestamp", round(time.time(), 0))

   r.hset("previous", "data", old_data)
   r.hset("previous", "timestamp", old_ts)

   logger.info("store_to_redis(): Publishing a message to the {} channel".format(REDIS_CHANNEL))
   r.publish(REDIS_CHANNEL, r.hget("current", "timestamp"))
   logger.info("store_to_redis(): Finished.")


def collect_chargepoint_data_by_interval(interval_in_seconds):
   while True:
      store_to_redis(get_current())
      logger.info("collect_chargepoint_data_by_interval(): sleeping for {} seconds.".format(interval_in_seconds))
      time.sleep(interval_in_seconds)

if __name__ == "__main__":
   collect_chargepoint_data_by_interval(300)