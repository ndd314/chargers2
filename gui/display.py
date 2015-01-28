from __future__ import print_function
from __future__ import division
from flask import Flask, render_template, jsonify, request
from flask.ext.cache import Cache
import redis
import logging
import os
import anyconfig
import json
import datetime
import time
from pprint import pprint
from webargs import Arg
from webargs.flaskparser import use_args, use_kwargs

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

credentials = anyconfig.load("private_config.json")['credentials']
garage_data = anyconfig.load("private_config.json")['garage_data']

r = redis.Redis(
    host=credentials['Redis']['server'],
    db=credentials['Redis']['database'],
    password=credentials['Redis']['password']
)

app = Flask(__name__)
app.debug = True

def find_avail(garage_name):
    current = json.loads(r.hget("current", "data"))
    return [station for station in current[garage_name]['stations'] if current[garage_name]['stations'][station] > 0]

def find_count(garage_name):
    current = json.loads(r.hget("current", "data"))
    total = 0
    for station in current[garage_name]['stations']:
        total += current[garage_name]['stations'][station]
    return total

def garages_for_company(company):
    garages = []
    current = json.loads(r.hget("current", "data"))
    for garage_name,garage_info in current.iteritems():
        if garage_info['company'] == company:
            garages.append(garage_name)
    return garages


def sites_for_garage(garage):
    return json.loads(r.hget("current", "data"))[garage]['stations']

@app.route("/get_all_garage_data")
def get_all():
    return jsonify(
        data=json.loads(r.hget("current", "data"))
    )

@app.route("/garage/<garage>/avail_stations")
def garage_avail(garage,use_json=True):
    if use_json:
        return jsonify(
            data=find_avail(garage)
        )
    else:
        return find_avail(garage)

@app.route("/garage/<garage>/avail_count")
def garage_count(garage):
    return jsonify(
        data=find_count(garage)
    )

@app.route("/garage")
def list_garage(use_json=True):
    if use_json:
        return jsonify(
            data=json.loads(r.hget("current", "data")).keys()
        )
    else:
        return json.loads(r.hget("current", "data")).keys()

@app.route("/")
def index():

    avails = {}
    for garage_name in list_garage(use_json=False):
        avails[garage_name] = garage_avail(garage_name, use_json=False)

    return render_template(
        "index.html",
        data=json.loads(r.hget("current", "data")),
        available=avails,
        time=datetime.datetime.fromtimestamp(json.loads(r.hget("current", "timestamp"))),
        server_time=datetime.datetime.fromtimestamp(time.time())
    )

@app.route("/garage/<garage_name>")
def garage(garage_name):
    avails = {}
    avails[garage_name] = garage_avail(garage_name, use_json=False)

    return render_template(
        "index.html",
        data={garage_name: json.loads(r.hget("current", "data"))[garage_name]},
        available=avails,
        time=datetime.datetime.fromtimestamp(json.loads(r.hget("current", "timestamp"))),
        server_time = datetime.datetime.fromtimestamp(time.time())
    )


@app.route("/company/<company_name>")
def company(company_name):

    avails = {}
    data = {}
    garage_names = garages_for_company(company_name)
    for garage_name in garage_names:
        avails[garage_name] = garage_avail(garage_name, use_json=False)
        data[garage_name] = json.loads(r.hget("current", "data"))[garage_name]

    return render_template(
        "index.html",
        data=data,
        available=avails,
        time=datetime.datetime.fromtimestamp(json.loads(r.hget("current", "timestamp"))),
        server_time=datetime.datetime.fromtimestamp(round(time.time(),0))
    )


user_args = {
    'target': Arg(str, required=True),  # 400 error thrown if
    # required argument is missing
    # Repeated parameter, e.g. "/?nickname=Fred&nickname=Freddie"
    'garages': Arg(str, multiple=True, required=True)
}

@app.route("/addsub")
@use_args(user_args)
def add_sub(user_args):
    if "target" in request.args:
        # We must be receiving the data
        for garage_name in user_args['garages']:
            for site in sites_for_garage(garage_name):
                r.sadd(site,user_args['target'])
    return render_template("addsub.html")

if __name__ == "__main__":
    port = int(os.getenv('VCAP_APP_PORT', '5000'))
    logging.info("Running on port {}".format(port))
    app.run(host='0.0.0.0', port=port)