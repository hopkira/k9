#
# Wolfram Mathmatica API Python Class

import requests
from secrets import *

class K9QA:
    """A class to simplify conversational acces to the Wolfram Mathematic API"""

    def __init__(self) -> None:
        """Initialise the Q&A instance with a default URL to start the conversation"""

        self.s = None
        self.base_url = "http://api.wolframalpha.com/v1/conversation.jsp"
        self.append_url = "/api/v1/conversation.jsp"
        self.conversationID = None
        self.geolocation = geolocation # defined in local secrets file
        self.appid = appid # defined in local secrets file
        # the secrets.py file will look something like:
        # appid = "XXXXXX-XXXXXXXXXX"
        # geolocation = "54.50,-1.34"

    def ask_question(self, question):
        """Exercises the API and stores conversation details between calls"""

        req_dict =  {}
        req_dict ['i'] = question
        req_dict['geolocation'] = self.geolocation
        req_dict['appid'] = self.appid 
        req_dict['units'] = "metric"
        req_dict['host'] = self.base_url
        if self.conversationID is not None:
            req_dict['conversationID'] = self.conversationID
        if self.s is not None:
            req_dict ['s'] = self.s
        # Are we in a conversation? If so then direct to correct host
        # and the right conversation
        r = requests.get(self.base_url, params = req_dict)
        # print(r.json())
        result = r.json()
        if 'error' in result :
            result['result'] = "I do not know the answer"
        if "Wolfram" in result['result']:
            result['result'] = "My name is K9. That question is irrelevant."
        if "conversationID" in result:
            self.conversationID = result["conversationID"]
        if "host" in result:
            self.base_url = "http://" + result["host"] + self.append_url
        if "s" in result:
            self.s = result["s"]
        if "result" in result:
            return result["result"]
        else:
            return "I do not understand."