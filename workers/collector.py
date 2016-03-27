from __future__ import print_function

from config import *
import logging
import anyconfig
import loggly.handlers

#TODO add logging and newrelic monitor

# logger = logging.getLogger('')
# logger.setLevel(logging.DEBUG)
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# loggly_handler = loggly.handlers.HTTPSHandler(url="{}{}".format(credentials["Loggly"]["url"], "workers"))
# loggly_handler.setLevel(logging.DEBUG)
# logger.addHandler(loggly_handler)
# logging.getLogger("newrelic").setLevel(logging.INFO)
# logging.getLogger("anyconfig").setLevel(logging.INFO)
# logging.getLogger("requests.packages.urllib3.connectionpool").setLevel(logging.INFO)

from changepoint import Charger, ChargePointConnection

import copy
import redis
import json
import time
import newrelic.agent

# newrelic.agent.initialize('newrelic.ini')
# application = newrelic.agent.register_application(timeout=10.0)

garage_data = anyconfig.load("garage_data.json")['garage_data']
cp = ChargePointConnection(CHARGEPOINT_USERNAME, CHARGEPOINT_PASSWORD)
r = redis.from_url(REDIS_URL)

@newrelic.agent.background_task()
def get_current():
    local_garage_data = copy.deepcopy(garage_data)
    for garage_name, garage_info in local_garage_data.iteritems():
        local_garage_data[garage_name][u'available_ports'] = 0
        # logger.debug("Starting with garage {}".format(garage_name))
        for charger in cp.get_vmware_stations(regex=garage_info['regex']):
            # logger.debug("Processing: {}:{}".format(garage_name,charger.sname))
            local_garage_data[garage_name]['stations'][charger.sname] = charger.port_count["available"]
            if 'available_ports' in local_garage_data[garage_name]:
                local_garage_data[garage_name][u'available_ports'] += charger.port_count["available"]
            else:
                local_garage_data[garage_name][u'available_ports'] = charger.port_count["available"]
    return local_garage_data

@newrelic.agent.background_task()
def store_to_redis(data):
    # logger.info("Updatng data and swapping current for previous in Redis store")
    string_data = json.dumps(data)

    old_ts = r.hget("current","timestamp")
    old_data = r.hget("current","data")

    r.hset("current","data",string_data)
    r.hset("current","timestamp", round(time.time(),0))

    r.hset("previous", "data", old_data)
    r.hset("previous", "timestamp", old_ts)

    # logger.info("Publishing a message to the {} channel".format(credentials['Redis']['channel']))
    r.publish(REDIS_CHANNEL,r.hget("current","timestamp"))

if __name__ == "__main__":
    while True:
        store_to_redis(get_current())
        time.sleep(300)
