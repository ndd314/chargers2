from __future__ import print_function
from __future__ import division
from flask import Flask, render_template, jsonify
from flask.ext.cache import Cache
from kairos import Timeseries
import json
import redis
import re
import logging
import os

logging.basicConfig(format='%(asctime)s: %(levelname)s %(module)s:%(funcName)s | %(message)s', level=logging.DEBUG)

config_redis = redis.Redis(
    os.getenv('REDIS_HOST_NAME'), int(os.getenv('REDIS_PORT')), db=int(os.getenv('CONFIG_DB')), password=os.getenv('REDIS_PASSWORD')
)

ts_redis = redis.Redis(
    os.getenv('REDIS_HOST_NAME'), int(os.getenv('REDIS_PORT')), db=int(os.getenv('TS_DB')),
    password=os.getenv('REDIS_PASSWORD')
)

intervals = json.loads(config_redis.get("intervals"))
credentials = json.loads(config_redis.get("credentials"))
garage_data = json.loads(config_redis.get("garage_data"))


app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

t = Timeseries(ts_redis, type='series', read_func=int, intervals=intervals)

@cache.memoize(timeout=30)
def gen_live_counts_for_charger(charger_name):
    charger_name = charger_name.replace(" ","-")
    logging.info("Querying for charger {}".format(charger_name))

    most_recent_timestamp = t.properties(charger_name)['minute']['last']
    timestamp, value = t.get(charger_name,"minute",timestamp=most_recent_timestamp,condense=True).popitem(last=True)
    value = value[0]
    logging.debug("Retrieved: {} @ {}".format(value, timestamp))
    return value

def gen_live_counts_for_garage(garage_name):
    garage_chargers = []
    for charger in garage_data[garage_name]['stations']:
        garage_chargers.append(gen_live_counts_for_charger(charger))
    return garage_chargers

def gen_summary_for_garage(garage_name):
    garage_data = gen_live_counts_for_garage(garage_name)
    avail_ports = 0
    for charger in garage_data:
        avail_ports += charger
    return {"avail_ports": avail_ports}

def gen_summary_for_company(company):
    counts = {}
    for garage in garage_data.keys():
        if garage_data[garage]['company'] == company:
            summary = gen_summary_for_garage(garage)
            counts[garage] = summary
    return counts

@app.route("/")
#@cache.cached(timeout=60)
def index():
    return render_template("index.html", vmware=gen_summary_for_company("VMware"), emc=gen_summary_for_company("EMC"), all_avail=get_all_avail())

def get_all_avail():
    all_avail = {}
    for garage in garage_data.keys():
        all_avail[garage] = get_avail(garage)
    return all_avail

def get_avail(garage):
    avail_chargers = []
    for station in garage_data[garage]['stations']:
        if gen_live_counts_for_charger(station) > 0:
            avail_chargers.append(re.sub("PG[1-3]-","",station))
    return avail_chargers

if __name__ == "__main__":
    port = int(os.getenv('VCAP_APP_PORT', '5000'))
    logging.info("Running on port {}".format(port))
    app.run(host='0.0.0.0', port=port)