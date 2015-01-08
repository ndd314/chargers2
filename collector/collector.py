from __future__ import print_function

from ChargePoint import Charger, ChargePointConnection
from kairos import Timeseries

import redis
import logging
import time
from pprint import pprint
import json
import os

logging.basicConfig(format='%(asctime)s: %(levelname)s %(module)s:%(funcName)s | %(message)s', level=logging.DEBUG)

config_redis = redis.Redis(
    os.getenv('REDIS_HOST_NAME'), int(os.getenv('REDIS_PORT')), db=int(os.getenv('CONFIG_DB')),
    password=os.getenv('REDIS_PASSWORD')
)

ts_redis = redis.Redis(
    os.getenv('REDIS_HOST_NAME'), int(os.getenv('REDIS_PORT')), db=int(os.getenv('TS_DB')),
    password=os.getenv('REDIS_PASSWORD')
)

intervals = json.loads(config_redis.get("intervals"))
credentials = json.loads(config_redis.get("credentials"))
garage_data = json.loads(config_redis.get("garage_data"))


t = Timeseries(
    ts_redis,
    type='series',
    read_func=int,
    intervals=intervals
)



cp = ChargePointConnection(credentials['ChargePoint']['user'],
                           credentials['ChargePoint']['password'],
                           credentials['ChargePoint']['chargepoint_login_url']
)

while True:
    for site_name in garage_data.keys():
        site = garage_data[site_name]
        logging.info("Processing site: {}".format(site['regex']))
        site_info = cp.get_stations_info(site['url'])
        for charger_dict in site_info:
            charger = Charger(charger_dict)
            logging.info("Processing charger: {}".format(charger.station_name))
            if site['regex'] not in charger.station_name[1]:
                logging.info("Skipping station {} because it failed to match filter string {}".format(charger.station_name,site['regex']))
            else:
                logging.debug("Pushing metric for {}".format(charger.station_name[1]))
                t.insert(
                    charger.station_name[1].replace(" ","-"),
                    charger.port_count['available']
                )
    time.sleep(300)
