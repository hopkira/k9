import requests

ENDPOINTS = {
    "stream": "bot/game/stream/{}",
    "move": "bot/game/{}/move/{}",
    "chat": "bot/game/{}/chat",
    "challenge": "challenge/{}"
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

    def _get_header(self, token):
        header = {
            "Authorization": "Bearer {}".format(token)
        }
        return header