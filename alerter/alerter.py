import anyconfig
from twilio.rest import TwilioRestClient
import sendgrid
import redis
from pprint import pprint
import logging
import re
import json

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

credentials = anyconfig.load("private_config.json")['credentials']
garage_data = anyconfig.load("private_config.json")['garage_data']


twilio_client = TwilioRestClient(
    credentials['Twilio']['account_sid'],
    credentials['Twilio']['auth_token']
)

sg = sendgrid.SendGridClient(
    credentials['SendGrid']['user'],
    credentials['SendGrid']['password']
)

r = redis.Redis(
    host=credentials['Redis']['server'],
    db=credentials['Redis']['database'],
    password=credentials['Redis']['password']
)
pubsub = r.pubsub()
pubsub.subscribe("alert")


def is_email(address):
    assert isinstance(address, str)
    return "@" in address


def is_phone(address):
    assert isinstance(address, str)
    address = address.replace("-", "")
    pattern = re.compile("^[\dA-Z]{3}[\dA-Z]{3}[\dA-Z]{4}$", re.IGNORECASE)
    return pattern.match(address) is not None


def send_alert(address, garage):
    if is_email(address):
        send_email(address, garage)
    elif is_phone(address):
        send_txt(address, garage)
    clear_subs_for_user(address)


def send_email(address, garage):
    logger.info("Sending email about {} to {}".format(garage, address))
    message = sendgrid.Mail()
    message.add_to(address)
    message.set_subject("{} has a new spot open, Hurry!".format(garage))
    message.set_text("Go get it!")
    message.set_from("matt@cowger.us")
    message.set_from_name("Chargers App")
    sg.send(message)


def send_txt(address, garage):
    logger.info("Sending txt about {} to {}".format(garage, address))
    twilio_client.messages.create(
        to=address,
        from_="+16504092352",
        body="{} has a new spot open. Hurry!".format(garage),
    )


def find_changes():
    current = json.loads(r.hget("current","data"))
    previous = json.loads(r.hget("previous","data"))

    cur_stations = {}
    prev_stations = {}
    for garage in current.itervalues():
        cur_stations.update(garage['stations'])

    for garage in previous.itervalues():
        prev_stations.update(garage['stations'])

    stations_with_new_spots = []
    for station_name in cur_stations.keys():
        if cur_stations[station_name] > prev_stations[station_name]:
            stations_with_new_spots.append(station_name)

    return stations_with_new_spots

def clear_subs_for_user(target):
    logger.debug("Clearing sub for user {}".format(target))
    for key in r.keys("SUB-*"):
        if r.type(key) == "set":
            r.srem(key,target)
            logger.debug("Removing user {} from subscription to {}".format(target,key))

while True:
    for item in pubsub.listen():
        if item['type'] == "message":
            logger.debug("received alert of new info with timstamp {}".format(item['data']))
            for station in find_changes():
                logger.info("Found new station {}...checking for subscriptions".format(station))
                if len(r.smembers("SUB-{}".format(station))) == 0:
                    logger.info("No notifications to send for station {}".format(station))
                for target in r.smembers("SUB-{}".format(station)):
                    logger.info("Found member to notifify for {}: {}".format(station, target))
                    send_alert(target, "{}".format(station))
