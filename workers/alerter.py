import logging
import anyconfig
import loggly.handlers
from keen.client import KeenClient  # TODO is this a mixpanel thing?
from config import *
from easy_sms import EasySms

# from twilio.rest import TwilioRestClient
import sendgrid
import redis
from pprint import pprint
import re
import json
import newrelic.agent

class Alerter:
   def __init__(self):
      self.logger = logging.getLogger()
      self.logger.setLevel(logging.DEBUG)
      self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
      logging.basicConfig()

      # loggly_handler = loggly.handlers.HTTPSHandler(url="{}{}".format(credentials["Loggly"]["url"], "alerter"))
      # loggly_handler.setLevel(logging.DEBUG)
      # logger.addHandler(loggly_handler)
      # logging.getLogger("newrelic").setLevel(logging.INFO)
      # logging.getLogger("anyconfig").setLevel(logging.INFO)
      # logging.getLogger("requests.packages.urllib3.connectionpool").setLevel(logging.INFO)

       #TODO loggly, newrelic

      # newrelic.agent.initialize('newrelic.ini')
      # application = newrelic.agent.register_application(timeout=10.0)

      self.garage_data = anyconfig.load("garage_data.json")['garage_data']

      # twilio_client = TwilioRestClient(
      #     credentials['Twilio']['account_sid'],
      #     credentials['Twilio']['auth_token']
      # )

      self.sg = sendgrid.SendGridClient(SENDGRID_USERNAME, SENDGRID_PASSWORD)

      # keen_client = KeenClient(
      #         project_id=credentials['Keen']['project_id'],
      #         write_key=credentials['Keen']['write_key'],
      #         read_key=credentials['Keen']['read_key'],
      #         master_key=credentials['Keen']['master_key']
      # )

   def is_email(self, address):
      assert isinstance(address, str)
      return "@" in address


   def is_phone(self, address):
      assert isinstance(address, str)
      address = address.replace("-", "")
      pattern = re.compile("^[\dA-Z]{3}[\dA-Z]{3}[\dA-Z]{4}$", re.IGNORECASE)
      return pattern.match(address) is not None


   @newrelic.agent.background_task()
   def send_alert(self, address, garage):
      if self.is_email(address):
         self.send_email(address, garage)
      elif self.is_phone(address):
         self.send_txt(address, garage)
      self.clear_subs_for_user(address)


   @newrelic.agent.background_task()
   def send_email(self, address, garage):
      logging.info("Sending email about {} to {}".format(garage, address))
      message = sendgrid.Mail()
      message.add_to(address)
      message.set_subject("{} has a new spot open, Hurry!".format(garage))
      message.set_text("Go get it!") #todo add how many spots are there
      message.set_from(SENDGRID_EMAIL_FROM)
      sg.send(message)


   @newrelic.agent.background_task()
   def send_txt(self, address, garage):
      logging.info("Sending txt about {} to {}".format(garage, address))
      body = "{} has a new spot open. Hurry!".format(garage),
      EasySms.send_sms(to=address, body=body)

      # twilio_client.messages.create(
      #     to=address,
      #     from_="+16504092352",
      #     body=body
      # )


   @newrelic.agent.background_task()
   def find_changes(self):
      current = json.loads(self.redis_con_alerter.hget("current", "data"))
      previous = json.loads(self.redis_con_alerter.hget("previous", "data"))

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

      all_changes = {}
      for station_name in cur_stations.keys():
         if cur_stations[station_name] != prev_stations[station_name]:
            all_changes[station_name] = cur_stations[station_name]

      if len(all_changes) > 0:
         logging.info("Chargers changes: {}".format(all_changes))
         # keen_client.add_event("chargers", all_changes)

      return stations_with_new_spots


   @newrelic.agent.background_task()
   def clear_subs_for_user(self, target):
      logging.debug("Clearing sub for user {}".format(target))
      for key in self.redis_con_alerter.keys("SUB-*"):
         if self.redis_con_alerter.type(key) == "set":
            self.redis_con_alerter.srem(key, target)
            logging.debug("Removing user {} from subscription to {}".format(target, key))


   @newrelic.agent.background_task()
   def main_loop(self):
      self.redis_con_alerter = redis.StrictRedis.from_url(REDIS_URL)
      pubsub = self.redis_con_alerter.pubsub()
      pubsub.subscribe(REDIS_CHANNEL)
      print "### pubsub_id: {}".format(id(pubsub))

      # todo add tests
      for item in pubsub.listen():
         self.logger.info("main_loop: Got a new alert. Processing now ...")
         if item['type'] == "message":
            logging.debug("received alert of new info with timstamp {}".format(item['data']))
            for station in self.find_changes():
               logging.info("Found new station {}...checking for subscriptions".format(station))
               if len(self.redis_con_alerter.smembers("SUB-{}".format(station))) == 0:
                  logging.info("No notifications to send for station {}".format(station))
               for target in self.redis_con_alerter.smembers("SUB-{}".format(station)):
                  logging.info("Found member to notifify for {}: {}".format(station, target))
                  self.send_alert(target, "{}".format(station))
         self.logger.info("main_loop: done processing alert.")

if __name__ == "__main__":
   Alerter.main_loop()
