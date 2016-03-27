import json
import urllib
import requests
from config import *

class EasySms:
   API_URL = EASYSMS_URL + "/messages"

   @classmethod
   def send_sms(self, to=None, body=None):
      message = { 'to' : to, 'body' : body }
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
      return response.json()['uid']