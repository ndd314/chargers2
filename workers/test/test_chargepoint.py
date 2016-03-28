from workers.changepoint import *
from config import *

import pytest
import sure
import vcr

charge_point = ChargePointConnection(CHARGEPOINT_USERNAME, CHARGEPOINT_PASSWORD)

@vcr.use_cassette('fixtures/vcr_cassettes/test_charge_point_get_stations_info.yaml', filter_post_data_parameters=['user_name', 'user_password'], match_on=['body'])
def test_get_stations_info():
   found_chargers = charge_point.get_vmware_stations("PG")
   len(found_chargers).should.equal(23)

# def test_get_stations_info_without_regex():
#    found_chargers = charge_point.get_vmware_stations()
#    len(found_chargers).should.equal(23)
