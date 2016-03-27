from workers.collector import *

import pytest
import sure
import vcr

@vcr.use_cassette('fixtures/vcr_cassettes/test_collector_get_current.yaml', filter_post_data_parameters=['user_name', 'user_password'])
def test_get_current():
   current_data = get_current()
   current_data['Central']['total_ports'].should.equal(13)