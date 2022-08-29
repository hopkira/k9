import requests

ENDPOINTS = {
    "profile": "account",
    "stream": "bot/game/stream/{}",
    "stream_event": "api/stream/event",
    "game": "bot/game/{}",
    "move": "bot/game/{}/move/{}",
    "chat": "/api/bot/game/{}/chat",
    "accept": "challenge/{}/accept",
    "decline": "challenge/{}/decline",
    "upgrade": "bot/account/upgrade",
    "challenge": "challenge/{}"
}

# docs: https://lichess.org/api
class Lichess():

    def __init__(self, token, url):
        self.header = self._get_header(token)
        self.baseUrl = url


    def get_game(self, game_id):
        url = self.baseUrl + ENDPOINTS["game"].format(game_id)
        r = requests.get(url, headers=self.header)

        if r.status_code != 200:
            print("Something went wrong! status_code: {}, response: {}".format(r.status_code, r.text))
            return None

        return r.json()

    def chat(self, game_id, room, text):
        payload = {"room": room, "text": text}
        url = self.baseUrl + ENDPOINTS["chat"].format(game_id)
        r = requests.post(url,headers = self.header, params=payload)

        if r.status_code != 200:
            print("Something went wrong! status_code: {}, response: {}".format(r.status_code, r.text))
            return None

        return r.json()

    def upgrade_to_bot_account(self):
        url = self.baseUrl + ENDPOINTS["upgrade"]
        r = requests.post(url, headers=self.header)

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


    def get_stream(self, game_id):
        url = self.baseUrl + ENDPOINTS["stream"].format(game_id)
        return requests.get(url, headers=self.header, stream=True)


    def get_event_stream(self):
        url = self.baseUrl + ENDPOINTS["stream_event"]
        return requests.get(url, headers=self.header, stream=True)


    def accept_challenge(self, challenge_id):
        url = self.baseUrl + ENDPOINTS["accept"].format(challenge_id)
        r = requests.post(url, headers=self.header)

        if r.status_code != 200:
            print("Something went wrong! status_code: {}, response: {}".format(r.status_code, r.text))
            return None

        return r.json()


    def decline_challenge(self, challenge_id):
        url = self.baseUrl + ENDPOINTS["decline"].format(challenge_id)
        r = requests.post(url, headers=self.header)

        if r.status_code != 200:
            print("Something went wrong! status_code: {}, response: {}".format(r.status_code, r.text))
            return None

        return r.json()

    def create_challenge(self, username:str, params:object):
        url = self.baseUrl + ENDPOINTS["challenge"].format(username)
        r = requests.post(url, headers=self.header, payload = params)

        if r.status_code != 200:
            print("Something went wrong! status_code: {}, response: {}".format(r.status_code, r.text))
            return None

        return r.json()


    def get_profile(self):
        url = self.baseUrl + ENDPOINTS["profile"]
        r = requests.get(url, headers=self.header)
        if r.status_code != 200:
            print("Something went wrong! status_code: {}, response: {}".format(r.status_code, r.text))
            return None

        return r.json()


    def _get_header(self, token):
        header = {
            "Authorization": "Bearer {}".format(token)
        }

        return header