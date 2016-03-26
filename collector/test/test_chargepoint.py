from collector.ChargePoint import *

import anyconfig
import urllib
import pytest
import sure

query_params = {
   "lat" : 37.39931348058685,
   "lng" : -122.1379984047241,
   "ne_lat" : 37.40442723948339,
   "ne_lng" : -122.11644417308042,
   "sw_lat" : 37.39419937272119,
   "sw_lng" : -122.15955263636778,
   "user_lat" : 37.8317378,
   "user_lng" : -122.20247309999999,
   "search_lat" : 37.4418834  ,
   "search_lng" : -122.14301949999998,
   "sort_by" : "distance",
   "f_estimationfee" : "false",
   "f_available" : "true",
   "f_inuse" : "true",
   "f_unknown" : "true",
   "f_cp" : "true",
   "f_other" : "true",
   "f_l3" : "false",
   "f_l2" : "true",
   "f_l1" : "false",
   "f_estimate" : "false",
   "f_fee" : "true",
   "f_free" : "false", # VMware stations are not free (free for first 4 hours, then $7/hour).
   "f_reservable" : "false",
   "f_shared" : "true",
   "driver_connected_station_only" : "false",
   "community_enabled_only" : "false",
   "_" : 1405380831644
}

credentials = anyconfig.load("private_config.json")['credentials']['ChargePoint']
search_url = "https://na.chargepoint.com/dashboard/getChargeSpots?" + urllib.urlencode(query_params)
charge_point = ChargePointConnection(credentials['user'], credentials['password'], credentials['chargepoint_login_url'])

def test_get_stations_info():
   found_chargers = charge_point.get_stations_info(search_url, "PG")
   len(found_chargers).should.equal(23)
