from __future__ import print_function
import logging
import json

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
            self.__setattr__(item,charger_dict[item])


class ChargePointConnection(object):

    def __init__(self, cpuser, cppassword, login_url):

        self._cpsession = requests.session()
        self._login_url = login_url
        self._cpuser = cpuser
        self._cppass = cppassword
        self._logged_in = False


    def _do_login(self):
        """

        :param cpuser: string
        :param cppassword: string
        :return: :rtype: boolean
        """

        form_data = {
            'user_name': self._cpuser,
            'user_password': self._cppass,
            'recaptcha_response_field': '',
            'timezone_offset': '480',
            'timezone': 'PST',
            'timezone_name': ''
        }
        auth = self._cpsession.post(url=self._login_url, data=form_data)
        self._logged_in = auth.json()['auth']


    def get_stations_info(self,url):
        """

        :param location: string
        :return: :rtype: list
        """

        logging.debug("Getting Data  from " + url)
        while not self._logged_in:
            self._do_login()
        station_data = self._cpsession.get(url)
        return json.loads(station_data.text)[0]['station_list']['summaries']