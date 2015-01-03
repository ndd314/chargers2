from __future__ import print_function
from static import sites
from ChargePoint import Charger, ChargePointConnection
from phant import Phant
import logging
import time


logging.basicConfig(format='%(asctime)s: %(levelname)s %(module)s:%(funcName)s | %(message)s', level=logging.DEBUG)

p = Phant("Qx4XBL7d5phdQw82K1b6in86vQM",
          'station_site', 'station_name', 'available', 'total',
          private_key='L3WvRqAbwpsbyBedlPaYi7La4Em',
          delete_key='jvrPmyVbxasg6X5YDBPjto87Y19',
          base_url="http://phant.exaforge.com:8080"
)

cp = ChargePointConnection('Matt@cowger.us','Habloo12')

while True:
    for site in sites:
        logging.info("Processing site: {}".format(site['filter_string']))
        site_info = cp.get_stations_info(site['url'])
        for charger_dict in site_info:
            charger = Charger(charger_dict)
            logging.info("Processing charger: {}".format(charger.station_name))
            p.log(charger.station_name[0], charger.station_name[1], charger.port_count['available'],
                    charger.port_count['total'])
    time.sleep(300)
