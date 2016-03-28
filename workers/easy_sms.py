import logging
import requests
from config import *

class EasySms:
   API_URL = EASYSMS_URL + "/messages"

   logging.basicConfig()
   logger = logging.getLogger()
   logger.setLevel(logging.INFO)

   @classmethod
   def send_sms(cls, to=None, body=None):
      message = { 'to' : to, 'body' : body }
      cls.logger.info("EasySms.send_sms(): texting {} with message".format(to, body))
      response = requests.session().post(url=EasySms.API_URL, data=message)

      # {
      #   "uid": "56f7d940d1471a0009000001",
      #   "to": "+14083935487",
      #   "from": null,
      #   "body": "this is a test",
      #   "status": "pending",
      #   "error_message": null,
      #   "c_at": "2016-03-27T12:59:44.424Z"
      # }

      response_json = response.json()
      cls.logger.info("EasySms.send_sms(): response = {}".format(response_json))
