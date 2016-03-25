from collector.ChargePoint import *

import anyconfig
import pytest
import sure

credentials = anyconfig.load("private_config.json")['credentials']['ChargePoint']
search_url = "https://na.chargepoint.com/dashboard/getChargeSpots?&lat=37.39041383851848&lng=-121.96937121940505&ne_lat=37.39105315337037&ne_lng=-121.9672026534165&sw_lat=37.3897745182144&sw_lng=-121.97153978539359&user_lat=37.83193351867604&user_lng=-122.20265718147691&search_lat=37.3881741&search_lng=-121.9793793&sort_by=distance&f_estimationfee=false&f_available=true&f_inuse=true&f_unknown=true&f_cp=true&f_other=true&f_l3=false&f_l2=true&f_l1=false&f_estimate=false&f_fee=true&f_free=true&f_reservable=false&f_shared=true&driver_connected_station_only=false&community_enabled_only=false&_=1405380831644"
charge_point = ChargePointConnection(credentials['user'], credentials['password'], credentials['chargepoint_login_url'])

def test_get_stations_info():
   found_chargers = charge_point.get_stations_info(search_url, "PG")
   len(found_chargers).should.equal(23)
