from workers.changepoint import *
from config import *

import pytest
import sure

charge_point = ChargePointConnection(CHARGEPOINT_USERNAME, CHARGEPOINT_PASSWORD)

def test_get_stations_info():
   found_chargers = charge_point.get_vmware_stations("PG")
   len(found_chargers).should.equal(23)

def test_get_stations_info_without_regex():
   found_chargers = charge_point.get_vmware_stations()
   len(found_chargers).should.equal(23)
