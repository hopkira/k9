from lichess import Lichess
import os

bot_token = os.getenv("LICHESS_BOT_TOKEN")
player_token = os.getenv("LICHESS_PLAYER_TOKEN")
stockfish_path = os.getenv("STOCKFISH_PATH")
username = os.getenv("LICHESS_USERNAME")
lichess_url = "https://lichess.org/api/"

li = Lichess(token=bot_token, url=lichess_url)

color = "white"

# player_token = str({"Authorization": "Bearer {}".format(player_token)})

params = {"rated": False, 
                "variant": "standard",
                "rated": "false",
                "clock.limit": "300",
                "clock.increment": "15",
                "color": "white",
                "acceptByToken": player_token,
                "keepAliveStream": "true"
                }

print(username, params)
response = li.create_challenge(username, params)
print(response)