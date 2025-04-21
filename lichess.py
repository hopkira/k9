#
# Forked from lichess-bot-devs/lichess bot
# Modified in 2025 to enable bot to monitor
# event stream and accept or decline challenge
#
import requests
from urllib.parse import urljoin

ENDPOINTS = {
    "stream": "bot/game/stream/{}",
    "stream_event": "stream/event",
    "move": "bot/game/{}/move/{}",
    "chat": "bot/game/{}/chat",
    "challenge": "challenge/{}",
    "accept": "challenge/{}/accept",
    "decline": "challenge/{}/decline"
}

# docs: https://lichess.org/api
class LichessAPI():

    def __init__(self, token, url):
        self.header = self._get_header(token)
        self.baseUrl = url

    def chat(self, game_id, room, text):
        payload = {"room": room, "text": text}
        url = self.baseUrl + ENDPOINTS["chat"].format(game_id)
        r = requests.post(url, headers = self.header, data = payload)
        if r.status_code != 200:
            print("Something went wrong! status_code: {}, response: {}".format(r.status_code, r.text))
            return None
        return r.json()

    def make_move(self, game_id, move):
        url = self.baseUrl + ENDPOINTS["move"].format(game_id, move)
        r = requests.post(url, headers=self.header)
        if r.status_code != 200:
            print("Something went wrong! status_code: {}, response: {}".format(r.status_code, r.text))
            return None
        return r.json()
    
    def get_event_stream(self):
        url = urljoin(self.baseUrl, ENDPOINTS["stream_event"])
        return requests.get(url, headers=self.header, stream=True)

    def get_stream(self, game_id):
        url = self.baseUrl + ENDPOINTS["stream"].format(game_id)
        return requests.get(url, headers=self.header, stream=True)

    def create_challenge(self, username, params):
        url = self.baseUrl + ENDPOINTS["challenge"].format(username)
        print(url)
        r = requests.post(url, headers=self.header, data = params)
        print(r.json())
        if r.status_code != 200:
            print("Something went wrong! status_code: {}, response: {}".format(r.status_code, r.text))
            return None
        return r.json()
    
    def accept_challenge(self, challenge_id):
        return self.api_post(ENDPOINTS["accept"].format(challenge_id))
    
    def decline_challenge(self, challenge_id, reason="generic"):
        return self.api_post(ENDPOINTS["decline"].format(challenge_id),
                             data=f"reason={reason}",
                             headers={"Content-Type":
                                      "application/x-www-form-urlencoded"},
                             raise_for_status=False)

    def _get_header(self, token):
        header = {
            "Authorization": "Bearer {}".format(token)
        }
        return header