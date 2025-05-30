#!/usr/bin/env python
# coding: utf-8
# Author: Richard Hopkins
# Date: 30 August 2022
#
# This program provides Lichess.com chess playing
# function for K9, optionally with the Phantom
# chess board (2025 revision)
#

import random
import os
import json
import time

import chess
import chess.engine
import chess.polyglot
import requests

from lichess import LichessAPI
from listen import Listen
from eyes import Eyes
from back_panel import BackLights
from ears import Ears
from voice import Voice
from memory import Memory
from tail import Tail

INFO_SCORE = 2

class ChessGame():
    '''Provides Lichess.com chess playing function'''

    def __init__(self):
        # Flag in Redis that K9 is in chess mode
        mem = Memory()
        mem.storeState("chess",1.0)
        # Initialize secrets from bashrc .profile
        bot_token = os.getenv("LICHESS_BOT_TOKEN")
        player_token = os.getenv("LICHESS_PLAYER_TOKEN")
        stockfish_path = os.getenv("STOCKFISH_PATH")
        self.username = os.getenv("LICHESS_USERNAME")
        # Initiialize lichess and stockfish
        lichess_url = "https://lichess.org/api/"
        self.li = LichessAPI(token=bot_token, url=lichess_url)
        self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        self.pieces = ("Pawn","Knight","Bishop","Rook","Queen","King")
        #bot = self.li.get_profile()
        self.board = chess.Board()
        self.game_id = None
        self.game_state = None
        self.context = {}
        #end_of_game = False
        #stop_now = False
        self.message = ""
        # Dictionary of phrases
        self.msgs = {
            "your_move": ("What's your move?","Your move!","You're up!","Your go!","It's your move!","It's your turn!","Your turn!","Your chance now","Over to you","Your turn now","Your turn to move"),
            "invalid_move": ("Invalid move","Sorry, invalid move","Incorrect move","That move is not valid","You have miscalculated, that is an invalid move","Move not valid","Improper move", "You are at fault - improper move", "Sorry you can't make that move"),
            "check": ("Check","You are in check","I have you in check","You're in check"),
            "winning": ("I think I'm winning","I'm now in front","This is looking good for me","My position looks strong","Things are looking negative for you","I am very happy with this game","It's not looking good for you","I like winning"),
            "takes": ("takes","captures","takes","triumphs over","takes","prevails over","takes","takes","destroys","seizes","traps","secures","gets","nabs"),
            "losing": ("I am losing, this is not good","You are a very good player","I'm feeling rather negative about this"),
            "mate_win": ("You should prepare for your end", "It's almost over for you", "The end is near for you", "I will mate soon","We are near the end of the game"),
            "mate_lose": ("this is not possible","how can I be losing?","you are the better player","this is not logical - I am losing"),
            "draw":  ("We are heading for a draw","The game is looking very even", "This is a well-balanced game", "We are drawing, who will make the winning move?"),
            "instruction": ("I have moved my","I will move","I've moved my","My move is")
        }
        # Create K9 interfaces
        self.eyes = Eyes()
        self.back = BackLights()
        self.listen = Listen()
        self.ears = Ears()
        self.voice = Voice()
        self.tail = Tail()
        # Initialize K9 interfaces
        print("Turning lights off...")
        self.eyes.off()
        self.back.off()
        self.ears.stop()
        print("Lights turned off...")

        '''
        # Ask what sise player wants to be
        self.player = self.ask_color()
        if self.player == chess.WHITE:
            bot_side = "black"
        else:
            bot_side = "white"
        self.send_player_msg("Affirmative. I will play " + str(bot_side))

        # Create Lichess game
        self.game_id = self.create_game(username=self.username, token=player_token, color=bot_side)

        gameStart Start of a game
        gameFinish Completion of a game
        challenge A player sends you a challenge or you challenge someone
        challengeCanceled A player cancels their challenge to you
        challengeDeclined The opponent declines your challenge
        '''
        self.terminated = False
        while not self.terminated:
            time.sleep(3.0)
            response = self.li.get_event_stream()
            lines = response.iter_lines()
            for line in lines:
                if line:
                        event = json.loads(line.decode("utf-8"))
                        print("Event: {}".format(event))
                        if event["type"] == "challenge":
                            print("Challenge detected...")
                            self.chlng_id = event["challenge"]["id"]
                            print("Challenge ID: {}".format(self.chlng_id))
                            self.li.accept_challenge(self.chlng_id)
                            print("Challenge accepted.")
                        if event["type"] == "gameStart":
                            self.game_id = event["game"]["id"]
                            print("Game ID: {}".format(self.game_id))
                            # Ask what sise player wants to be
                            bot_side = event["game"]["color"]
                            if bot_side == "black":
                                self.player = chess.WHITE
                            else:
                                self.player = chess.BLACK
                            self.send_player_msg("Affirmative. I will play " + str(bot_side))
                            self.terminated = True
                            break
        # Play Lichess game
        print("Starting game...")
        self.play_game(game_id=self.game_id)
        # Game finished
        self.engine.quit()
        print(self.board)
        if self.board.is_checkmate():
            if self.board.turn == self.player:
                self.send_player_msg("Checkmate - I have won")
                self.tail.wag_h()
            else:
                self.send_player_msg("Congratulations - you have won")
                self.tail.down()
        if self.board.is_stalemate():
            self.message = "We have drawn through stalemate"
            self.tail.center()
        if self.board.is_insufficient_material(): 
            self.message = "A draw is now inevitable due to insufficient material."
            self.tail.center()
        if self.board.is_seventyfive_moves(): 
            self.message = "I am really bored.  We have drawn through repetition." 
            self.tail.center()
        if self.board.is_fivefold_repetition():
            self.message= "The game is over, it has been drawn through repetition." 
            self.tail.center()
        self.send_player_msg(self.message)
        self.send_player_msg("Thank you for a lovely game")
        mem.storeState("chess",0.0)

    def ask_color(self):
        '''Ask player what color they would like to play'''
        self.send_player_msg("Would you like to play black or white?")
        while True:
            # bot_side = input ("Do you want to play black or white? ")
            player_side = self.listen.listen_for_command()
            print("I heard: " + player_side)
            if "white" in player_side:
                player = chess.WHITE
                return player
            if "black" in player_side:
                player = chess.BLACK
                return player

    def update_board(self, board, move):
        '''Update the UCI/Stockfish board in line with the Lichess board state'''
        uci_move = chess.Move.from_uci(move)
        if board.is_legal(uci_move):
            self.board.push(uci_move)
        else:
            print('Ignoring illegal move {} on board {}'.format(move, board.fen()))
        return self.board
    
    def create_game(self, username, token:str, color:str):
        '''Create a Lichess game and return game_id'''
        params = {"rated": False, 
                        "variant": "standard",
                        "rated": "false",
                        "clock.limit": "300",
                        "clock.increment": "15",
                        "color": color,
                        "acceptByToken": token,
                        "keepAliveStream": "true"
                        }
        try:
            response = self.li.create_challenge(username, params)
            # nb, as we used token, challenge_id may be game_id
            game_id = response.get("game", {}).get("id")
            print("GameID:",game_id)
            return game_id
        except Exception:
            print("Could not create game")
            return None

    def play_game(self, game_id:str):
        with chess.polyglot.open_reader("./Titans.bin") as reader:
            '''Play a created Lichess game'''
            stream = self.li.get_stream(game_id)
            lines = stream.iter_lines()
            initial_state = json.loads(next(lines).decode('utf-8'))
            self.game_state = initial_state.get("state")
            print("Initial state:",str(self.game_state))
            moves = self.game_state["moves"].split()
            print("Moves:",moves)
            print("Status:",self.game_state["status"])
            try:
                while self.game_state["status"] == "started":
                    try:
                        binary_chunk = next(lines)
                    except StopIteration:
                        print("Game finished")
                        return
                    event_obj = json.loads(binary_chunk.decode("utf-8")) if binary_chunk else None
                    print("Event:",str(event_obj))
                    if event_obj is not None:
                        if event_obj["type"] == 'gameState':
                            self.game_state = event_obj
                            moves = self.game_state["moves"].split()
                            print("Moves:",moves)
                            self.board = chess.Board()
                            for move in moves:
                                self.board = self.update_board(self.board, move)
                            print(self.board)
                            if self.board.turn == self.player:
                                # analyse the board
                                if self.board.is_check(): 
                                    self.tail.up()
                                    self.send_player_msg(self.random_msg("check")) # announce check
                                result = self.engine.analyse(board=self.board, limit=chess.engine.Limit(time=1.0),info=INFO_SCORE)
                                print(result)
                                #score = result.score.pov(chess.WHITE)
                                score = result['score'].pov(chess.WHITE)
                                print("Analysis score:", score)
                                # prompt player for their move
                                self.send_player_msg(self.random_msg("your_move"))
                            else:
                                self.back.on()
                                self.eyes.on()
                                self.ears.think()
                                # Try to find the best book move
                                try:
                                    book_move = reader.find(board=self.board)
                                except IndexError:
                                    book_move = None
                                if book_move is None:
                                    result = self.engine.play(board=self.board, limit=chess.engine.Limit(time=10.0),info=INFO_SCORE)
                                    print("Result: {}".format(result))
                                    move = result.move
                                    print("Out of book moves!")
                                    print("Stockfish Move: {}".format(move))
                                    score = result.info['score'].pov(chess.WHITE)
                                else:
                                    result = self.engine.analyse(board=self.board, limit=chess.engine.Limit(time=2.0),info=INFO_SCORE)
                                    print("Result: {}".format(result))
                                    move = book_move.move
                                    print("Book Move: {}".format(move))
                                    score = result["score"].pov(chess.WHITE)
                                print("Final Move: {}".format(move))
                                print("White's score: {}".format(score))
                                self.back.off()
                                self.ears.stop()
                                self.li.make_move(game_id=game_id,move=move)
                                move_piece = self.pieces[self.board.piece_type_at(move.from_square)-1] 
                                move_color = self.board.turn
                                move_from = chess.SQUARE_NAMES[move.from_square]
                                move_to = chess.SQUARE_NAMES[move.to_square]  
                                if 'score' in self.context:
                                    old_score = self.context["score"]
                                    self.context.update(old_score = old_score)
                                # Announce if piece is taken
                                taken = self.board.piece_type_at(move.to_square)
                                if taken is not None:
                                    if (self.board.turn == self.player):
                                        if (random.random() < (taken*0.2)):
                                            self.send_player_msg("You have taken my " + self.pieces[taken-1])
                                            self.tail.down()
                                    else:
                                        self.send_player_msg("My " + move_piece + " " + self.random_msg("takes") + " your " + self.pieces[taken-1])
                                        self.tail.up()
                                # if no piece is taken, announce K9's move
                                else:
                                    if (self.board.turn != self.player):
                                        self.send_player_msg(self.random_msg("instruction") + " " + move_piece + " from " + move_from + " to " + move_to)
                                self.context.update(player = self.player,
                                            mv_color = move_color,
                                            mv_from = move_from,
                                            mv_to = move_to,
                                            score = score,
                                            piece = move_piece)
                                # number = 3 and random 0.8
                                if ((self.board.fullmove_number > 3) and (random.random()>0.7)): self.send_player_msg(self.get_phrase())
                                self.eyes.set_level(0.1)
            except requests.exceptions.StreamConsumedError:
                print("Game aborted by player")
                return
            print("Game finished")
            return

    def send_player_msg(self, command:str):
        '''Send a player a message via chat and verbally via the robot'''
        if self.game_id is not None:
            self.li.chat(game_id=self.game_id, room="player", text=command)
        self.voice.speak(command)

    def get_phrase(self):
        '''Determine appropriate phrase based on context'''
        if (self.context['score'].is_mate()):
            self.context.update(to_mate = self.context['score'].mate())
            if self.context['player']:
                # human player is white
                if self.context['to_mate'] >= 0:
                    self.tail.down()
                    return self.random_msg("mate_lose")
                if self.context['to_mate'] < 0: 
                    self.tail.wag_v()
                    return self.random_msg("mate_win")
            else:
                if self.context['to_mate'] >= 0:
                    self.tail.wag_v()
                    return self.random_msg("mate_win")
                if self.context['to_mate'] < 0:
                    self.tail.down()
                    return self.random_msg("mate_lose")
        else:
            self.context.pop('to_mate', None)
            return self.interpret_score(self.context['score'].score())

    def interpret_score(self, score):
        '''React to how well (or poorly) the opponent is playing'''
        if self.context['player']:
            if score > 60:
                self.tail.down()
                return self.random_msg("losing")
            if score < -60:
                self.tail.up()
                return self.random_msg("winning")
        else:
            if score > 60:
                self.tail.up()
                return self.random_msg("winning")
            if score < -60:
                self.tail.down()
                return self.random_msg("losing")
        self.tail.center()
        return self.random_msg("draw")

    def get_color(self, bool):
        '''Return black or white based on UCI color value'''
        string = "white" if bool else "black"
        return string

    def random_msg(self, phrase:str) -> str:
        '''Return a relevant random phrase from the phrase dictionary'''
        phrase_dict = self.msgs[phrase]
        length = len(phrase_dict)
        index = random.randint(0,length-1)
        message = phrase_dict[index] 
        return message

if __name__ == "__main__":
    game = ChessGame()
else:
    print ("K9 chess module imported")