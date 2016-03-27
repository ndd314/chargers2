import json
import urllib
import requests

class Charger(object):
   @classmethod
   def get_class_name(cls):
      return cls.__name__

   def __str__(self):
      # to show include all variables in sorted order
      return "<{}>@0x{}:\n".format(self.get_class_name(), id(self)) + "\n".join(
         ["  %s: %s" % (key.rjust(30), self.__dict__[key]) for key in sorted(set(self.__dict__))])

   def __repr__(self):
      return self.__str__()

   def __init__(self, charger_dict):
      for item in charger_dict.keys():
         self.__setattr__(item, charger_dict[item])

   @property
   def sname(self):
      return self.station_name[1]

class ChargePointConnection(object):
   VMWARE_SEARCH_PARAMS = {
      "ne_lat": 37.40442723948339,
      "ne_lng": -122.11644417308042,
      "sw_lat": 37.39419937272119,
      "sw_lng": -122.15955263636778,
      "f_available": "true",
      "f_inuse": "true",
      "f_cp": "true",
      "f_l2": "true",
      "f_free": "false",  # VMware stations are not free (free for first 4 hours, then $7/hour).
      # "lat" : 37.39931348058685,
      # "lng" : -122.1379984047241,
      # "user_lat" : 37.8317378,
      # "user_lng" : -122.20247309999999,
      # "search_lat" : 37.4418834  ,
      # "search_lng" : -122.14301949999998,
      # "sort_by" : "distance",
      # "f_estimationfee" : "false",
      # "f_unknown" : "true",
      # "f_other" : "true",
      # "f_l3" : "false",
      # "f_l1" : "false",
      # "f_estimate" : "false",
      # "f_fee" : "true",
      # "f_reservable" : "false",
      # "f_shared" : "true",
      # "driver_connected_station_only" : "false",
      # "community_enabled_only" : "false",
      # "_" : 1405380831644
   }

   LOGIN_URL = "https://na.chargepoint.com/users/validate"
   SEARCH_URL = "https://na.chargepoint.com/dashboard/getChargeSpots?" + urllib.urlencode(VMWARE_SEARCH_PARAMS)

   def __init__(self, cpuser, cppassword):
      self.__cpsession = requests.session()
      self.__cpuser = cpuser
      self.__cppass = cppassword
      self.__logged_in = False

   def __form_data(self):
      return {
         'user_name': self.__cpuser,
         'user_password': self.__cppass,
      }

   def __login(self):
      if self.__logged_in:
         return
      response = self.__cpsession.post(url=ChargePointConnection.LOGIN_URL, data=self.__form_data())
      self.__logged_in = response.json()['auth']

   def get_vmware_stations(self, regex=None):
      while not self.__logged_in:
         self.__login()

      station_data = self.__cpsession.get(ChargePointConnection.SEARCH_URL)
      all_chargers = []
      for charger in json.loads(station_data.text)[0]['station_list']['summaries']:
         charger_obj = Charger(charger)
         if regex in charger_obj.sname:
            all_chargers.append(charger_obj)

      return all_chargers
