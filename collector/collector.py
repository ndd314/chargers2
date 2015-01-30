from __future__ import print_function

import logging

logging.basicConfig(format='%(asctime)s: %(levelname)s %(module)s:%(funcName)s | %(message)s', level=logging.DEBUG)

from ChargePoint import Charger, ChargePointConnection



import anyconfig
import copy
import redis
import json
import time
import newrelic.agent

newrelic.agent.initialize('newrelic.ini')
application = newrelic.agent.register_application(timeout=10.0)

credentials = anyconfig.load("private_config.json")['credentials']
garage_data = anyconfig.load("private_config.json")['garage_data']

cp = ChargePointConnection(credentials['ChargePoint']['user'],
                           credentials['ChargePoint']['password'],
                           credentials['ChargePoint']['chargepoint_login_url']
)

r = redis.Redis(
    host=credentials['Redis']['server'],
    db=credentials['Redis']['database'],
    password=credentials['Redis']['password']
)


@newrelic.agent.background_task()
def get_current():

    local_garage_data = copy.deepcopy(garage_data)
    for garage_name, garage_info in local_garage_data.iteritems():
        logging.debug("Starting with garage {}".format(garage_name))
        for charger in cp.get_stations_info(garage_info['url'], regex=garage_info['regex']):
            logging.debug("Processing: {}:{}".format(garage_name,charger.sname))
            local_garage_data[garage_name]['stations'][charger.sname] = charger.port_count["available"]
            if 'available_ports' in local_garage_data[garage_name]:
                local_garage_data[garage_name][u'available_ports'] += charger.port_count["available"]
            else:
                local_garage_data[garage_name][u'available_ports'] = charger.port_count["available"]
    return local_garage_data


@newrelic.agent.background_task()
def store_to_redis(data):
    logging.info("Updatng data and swapping current for previous in Redis store")
    string_data = json.dumps(data)

    old_ts = r.hget("current","timestamp")
    old_data = r.hget("current","data")


    r.hset("current","data",string_data)
    r.hset("current","timestamp", round(time.time(),0))

    r.hset("previous", "data", old_data)
    r.hset("previous", "timestamp", old_ts)

    logging.info("Publishing a message to the {} channel".format(credentials['Redis']['channel']))
    r.publish(credentials['Redis']['channel'],r.hget("current","timestamp"))

if __name__ == "__main__":
    while True:
        store_to_redis(get_current())
        time.sleep(60)
