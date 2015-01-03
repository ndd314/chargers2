from __future__ import print_function
from __future__ import division
from flask import Flask, render_template, jsonify
from flask.ext.cache import Cache
from phant import Phant
from pprint import pprint

import logging
import os

logging.basicConfig(format='%(asctime)s: %(levelname)s %(module)s:%(funcName)s | %(message)s', level=logging.DEBUG)

garage_data = {
    "Creekside": {
          'regex': 'PG3',
          'stations': ['PG3-STATION 19', 'PG3-STATION 20', 'PG3-STATION 21','PG3-STATION 22', 'PG3-STATION 23',
                       'PG3-STATION 24', 'PG3-STATION 25', 'PG3-STATION 26'],
          'company': 'VMware'
        },
    "Hilltop": {
        'regex': 'PG1',
        'stations': ['PG1-STATION 11', 'PG1-STATION 12', 'PG1-STATION 13', 'PG1-STATION 14', 'PG1-STATION 15',
                     'PG1-STATION 16', 'PG1-STATION 17', 'PG1-STATION 18'],
        'company': 'VMware'
        },
    "Central": {
        'regex': 'PG2',
        'stations': ['PG2-STATION 01', 'PG2-STATION 02', 'PG2-STATION 03', 'PG2-STATION 04', 'PG2-STATION 05',
                     'PG2-STATION 06', 'PG2-STATION 07'],
        'company': 'VMware'
    },
    "Santa_Clara": {
        'regex': 'SANTA',
        'stations': ['SANTA'],
        'company': 'EMC'
    },
    "DPAD": {
        'regex': 'MISSIONCOLLEGE',
        'stations': ['MISSIONCOLLEGE1', 'MISSIONCOLLEGE2', 'MISSIONCOLLEGE3', 'MISSIONCOLLEGE4', 'MISSIONCOLLEGE5'],
        'company': 'EMC'
    },
}

p = Phant("Qx4XBL7d5phdQw82K1b6in86vQM",
          'station_site', 'station_name', 'available', 'total',
          base_url="http://phant.exaforge.com:8080"
)

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@cache.memoize(timeout=300)
def gen_live_counts_for_charger(charger_name):
    live = p.get(
        limit=1,
        grep=('station_name',charger_name)
    )
    return live[0]

def gen_live_counts_for_garage(garage_name):
    garage_chargers = []
    for charger in garage_data[garage_name]['stations']:
        garage_chargers.append(gen_live_counts_for_charger(charger))
    return garage_chargers

def gen_summary_for_garage(garage_name):
    garage_data = gen_live_counts_for_garage(garage_name)
    total_ports = 0
    avail_ports = 0
    for charger in garage_data:
        total_ports += int(charger['total'])
        avail_ports += int(charger['available'])
    percent = int(round((avail_ports / total_ports) * 100,0))
    return {"avail_ports": avail_ports, "total_ports": total_ports, "percent": percent}

def gen_summary_for_company(company):
    counts = {}
    for garage in garage_data.keys():
        if garage_data[garage]['company'] == company:
            summary = gen_summary_for_garage(garage)
            counts[garage] = summary
    return counts

@app.route("/")
@cache.cached(300)
def index():
    return render_template("index.html", vmware=gen_summary_for_company("VMware"), emc=gen_summary_for_company("EMC"))

@app.route("/get_avail_chargers/<garage>")
def get_avail(garage):
    avail_chargers = []
    data = gen_live_counts_for_garage(garage)
    for charger in data:
        if int(charger['available']) > 0:
            avail_chargers.append(charger['station_name'])
    return jsonify({'chargers': avail_chargers})

if __name__ == "__main__":
    port = int(os.getenv('VCAP_APP_PORT', '5000'))
    logging.info("Running on port {}".format(port))
    app.run(host='0.0.0.0', port=port)