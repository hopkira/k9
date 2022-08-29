from lichess import Lichess
import os
import json
import time
import requests
import sys
import chess
import chess.engine

class Game:
    def __init__(self, json, username, base_url, abort_time):
        self.username = username
        self.id = json.get("id")
        self.speed = json.get("speed")
        clock = json.get("clock") or {}
        ten_years_in_ms = 1000 * 3600 * 24 * 365 * 10
        self.clock_initial = clock.get("initial", ten_years_in_ms)
        self.clock_increment = clock.get("increment", 0)
        self.perf_name = (json.get("perf") or {}).get("name", "{perf?}")
        self.initial_fen = json.get("initialFen")
        self.state = json.get("state")
        self.base_url = base_url
        self.abort_at = time.time() + abort_time
        self.terminate_at = time.time() + (self.clock_initial + self.clock_increment) / 1000 + abort_time + 60
        self.disconnect_at = time.time()

    def is_abortable(self):
        return len(self.state["moves"]) < 6

    def ping(self, abort_in, terminate_in, disconnect_in):
        if self.is_abortable():
            self.abort_at = time.time() + abort_in
        self.terminate_at = time.time() + terminate_in
        self.disconnect_at = time.time() + disconnect_in

    def should_abort_now(self):
        return self.is_abortable() and time.time() > self.abort_at

    def should_terminate_now(self):
        return time.time() > self.terminate_at

    def should_disconnect_now(self):
        return time.time() > self.disconnect_at

    def my_remaining_seconds(self):
        return (self.state["wtime"] if self.is_white else self.state["btime"]) / 1000

    def __str__(self):
        return f"{self.url()} {self.perf_name} vs {self.opponent.__str__()}"

    def __repr__(self):
        return self.__str__()


bot_token = os.getenv("LICHESS_BOT_TOKEN")
player_token = os.getenv("LICHESS_PLAYER_TOKEN")
stockfish_path = os.getenv("STOCKFISH_PATH")
username = os.getenv("LICHESS_USERNAME")
lichess_url = "https://lichess.org/api/"

li = Lichess(token=bot_token, url=lichess_url)

engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
INFO_SCORE = 2

def update_board(board, move):
    uci_move = chess.Move.from_uci(move)
    if board.is_legal(uci_move):
        board.push(uci_move)
    else:
        print('Ignoring illegal move {} on board {}'.format(move, board.fen()))
    return board

# player_token = str({"Authorization": "Bearer {}".format(player_token)})

params = {"rated": False, 
                "variant": "standard",
                "rated": "false",
                "clock.limit": "300",
                "clock.increment": "15",
                "color": "black",
                "acceptByToken": player_token,
                "keepAliveStream": "true"
                }

player = chess.WHITE

print(username, params)
response = li.create_challenge(username, params)
game_id = response.get("game", {}).get("id")
print("GameID:",game_id)
stream = li.get_stream(game_id)
lines = stream.iter_lines()
print("Lines:",str(lines))
initial_state = json.loads(next(lines).decode('utf-8'))
print("Initial state:",str(initial_state))
game = Game(initial_state, username, li.baseUrl, 20)
moves = game.state["moves"].split()
print("Moves:",moves)
try:
    while True:
        for event in stream:
            event_json = event.decode('utf8').replace("'", '"')
            print(event_json)
            if event_json != "\n":
                event_obj = json.loads(event_json)
                if event_obj["type"] == 'gameState':
                    game.state = event_obj
                    moves = game.state["moves"].split()
                    print("Moves:",moves)
                    board = chess.Board()
                    for move in moves:
                        board = update_board(board, move)
                    print(board)
            if board.turn != player:
                result = engine.play(board=board, limit=chess.engine.Limit(time=20.0),info=INFO_SCORE)

except requests.exceptions.StreamConsumedError:
    print("Game aborted by player")
    sys.exit(0)