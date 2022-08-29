from lichess import Lichess
import requests
import os

bot_token = os.getenv("LICHESS_BOT_TOKEN")
player_token = os.getenv("LICHESS_PLAYER_TOKEN")
stockfish_path = os.getenv("STOCKFISH_PATH")
username = os.getenv("LICHESS_USERNAME")
lichess_url = "https://lichess.org/api/"

li = Lichess(token=bot_token, url=lichess_url)

color = "white"
side = "white"

player_token = str({"Authorization": "Bearer {}".format(player_token)})

def create_game(username, token, color):
    params = {"rated": False, 
                "variant": "standard",
                "clock.limit": 300.0,
                "clock.increment": 15,
                "color": color,
                "acceptByToken": token
                }
    print(username, params)
    response = li.create_challenge(username, params)
    print(response)

create_game(username=username, token=player_token, color=side)