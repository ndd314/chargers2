from collector.collector import *

import pytest
import sure

def test_get_current():
   current_data = get_current()
   current_data['Central']['total_ports'].should.equal(13)