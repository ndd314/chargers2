import logging
import anyconfig
from keen.client import KeenClient
from config import *
from easysms import EasySms

import sendgrid
import redis
import re
import json
import newrelic.agent

class Alerter:
   def __init__(self):
      logging.basicConfig()
      self.logger = logging.getLogger()
      self.logger.setLevel(logging.INFO)
      self.garage_data = anyconfig.load("garage_data.json")['garage_data']
      self.sg = sendgrid.SendGridClient(SENDGRID_USERNAME, SENDGRID_PASSWORD)
      self.keen_client = KeenClient(
         project_id=KEEN_PROJECT_ID,
         write_key=KEEN_WRITE_KEY,
         read_key=KEEN_READ_KEY,
         base_url=KEEN_API_URL
      )

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
      self.logger.info("send_email(): Sending email about {} to {}".format(garage, address))
      message = sendgrid.Mail()
      message.add_to(address)
      message_text = "{} has a new spot open".format(garage)
      message.set_subject(message_text)
      message.set_text(message_text) #todo add how many spots are there
      message.set_from(SENDGRID_EMAIL_FROM)
      self.sg.send(message)


   @newrelic.agent.background_task()
   def send_txt(self, address, garage):
      self.logger.info("send_txt(): Sending txt about {} to {}".format(garage, address))
      body = "{} has a new spot open".format(garage),
      EasySms.send_sms(to=address, body=body)


   @newrelic.agent.background_task()
   def find_changes(self):
      current = json.loads(self.redis_connection.hget("current", "data"))
      previous = json.loads(self.redis_connection.hget("previous", "data"))

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

      self.logger.info("find_changes(): all chargers changes: {}".format(all_changes))

      if len(all_changes) > 0:
         self.logger.info("find_changes(): sending keen events: {}".format(all_changes))
         self.keen_client.add_event("chargers", all_changes)

      self.logger.info("find_changes(): stations with new spots {}".format(stations_with_new_spots))
      return stations_with_new_spots


   @newrelic.agent.background_task()
   def clear_subs_for_user(self, target):
      self.logger.info("clear_subs_for_user(): Clearing sub for user {}".format(target))
      for key in self.redis_connection.keys("SUB-*"):
         if self.redis_connection.type(key) == "set":
            self.redis_connection.srem(key, target)
            self.logger.info("clear_subs_for_user(): Removing user {} from subscription to {}".format(target, key))

   def find_garage(self, station):
      # station = PG3-STATION 26 for example
      # PG1 is Hilltop, PG2 is Central, PG3 is Creekside
      garages = ['Hilltop', 'Central', 'Creekside']
      garage_array_index = int(station[2]) - 1
      return garages[garage_array_index]


   @newrelic.agent.background_task()
   def main_loop(self):
      self.redis_connection = redis.StrictRedis.from_url(REDIS_URL)
      pubsub = self.redis_connection.pubsub()
      pubsub.subscribe(REDIS_CHANNEL)

      # todo add tests
      for item in pubsub.listen():
         self.logger.info("alerter.main_loop(): Got a new alert. Processing ...")

         if item['type'] == "message":
            self.logger.info("alerter.main_loop(): received alert of new info with timstamp {}".format(item['data']))

            for station in self.find_changes():
               self.logger.info("alerter.main_loop(): Found new station {}...checking for subscriptions".format(station))

               garage_name = self.find_garage(station)
               queue_name = "SUB-{}".format(garage_name)

               self.logger.info("alerter.main_loop(): Checking queue {} for members".format(queue_name))
               queue_members = self.redis_connection.smembers(queue_name)

               if len(queue_members) == 0:
                  self.logger.info("alerter.main_loop(): No notifications to send for garage {}".format(garage_name))
               for target in queue_members:
                  self.logger.info("alerter.main_loop(): Notifying {} for {} changes.".format(target, garage_name))
                  self.send_alert(target, garage_name)

         self.logger.info("alerter.main_loop(): done processing alert.")

if __name__ == "__main__":
   Alerter.main_loop()
