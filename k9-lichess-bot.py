import chess
import chess.engine
import random

from k9tts import speak
from listen import Listen
from eyes import Eyes
from back_lights import BackLights
from ears import Ears
from voice import Voice
from memory import Memory as mem

engine = chess.engine.SimpleEngine.popen_uci("./stockfish")

INFO_SCORE = 2
    
board = chess.Board()

pieces = ("Pawn","Knight","Bishop","Rook","Queen","King")
message = ""

your_move = ("What's your move?","Your move!","You're up!","Your go!","It's your move!","It's your turn!","Your turn!","Your chance now","Over to you","Your turn now","Your turn to move")
invalid_move = ("Invalid move","Sorry, invalid move","Incorrect move","That move is not valid","You have miscalculated, that is an invalid move","Move not valid","Improper move", "You are at fault - improper move", "Sorry you can't make that move")
check = ("Check","You are in check","I have you in check","You're in check")
winning = ("I think I'm winning","I'm now in front","This is looking good for me","My position looks strong","Things are looking negative for you","I am very happy with this game","It's not looking good for you","I like winning")
takes = ("takes","captures","takes","triumphs over","takes","prevails over","takes","takes","destroys","seizes","traps","secures","gets","nabs")
losing = ("I am losing, this is not good","You are a very good player","I'm feeling rather negative about this")
mate_win = ("You should prepare for your end", "It's almost over for you", "The end is near for you", "I will mate soon","We are near the end of the game")
mate_lose = ("this is not possible","how can I be losing?","you are the better player","this is not logical - I am losing")
draw = ("We are heading for a draw","The game is looking very even", "This is a well-balanced game", "We are drawing, who will make the winning move?")
instruction = ("Please move my","I will move","I will move my","My move is")
context = {}

def get_phrase():
    if (context['score'].is_mate()):
        context.update(to_mate = context['score'].mate())
        if context['player']:
            # human player is white
            if context['to_mate'] >= 0: return random_msg(mate_lose)
            if context['to_mate'] < 0: return random_msg(mate_win)
        else:
            if context['to_mate'] >= 0: return random_msg(mate_win)
            if context['to_mate'] < 0: return random_msg(mate_lose)
    else:
        context.pop('to_mate', None)
        return interpret_score(context['score'].score())

def interpret_score(score):
    if context['player']:
        if score > 60: return random_msg(losing)
        if score < -60: return random_msg(winning)
    else:
        if score > 60: return random_msg(winning)
        if score < -60: return random_msg(losing)
    return random_msg(draw)

def get_color(bool):
    string = "white" if bool else "black"
    return string

def random_msg(phrase_dict):
    length = len(phrase_dict)
    index = random.randint(0,length-1)
    message = phrase_dict[index] 
    return message

def speak(command:str):
    k9voice.speak(command)
    # put something in the lichess chat

stop_now = False

k9eyes = Eyes()
k9back = BackLights()
k9listen = Listen()
k9ears = Ears()
k9voice = Voice()

print("Turning lights off...")
k9eyes.off()
k9back.off()
print("Lights turned off...")

# SET UP GAME

'''
speak("what is your name?")
name = k9listen.listen_for_command()
# name = input ("What is your name? ")
speak("Hello " + str(name) + "!")

speak("Do you want to play black or white?")

while True:
    # side = input ("Do you want to play black or white? ")
    side = k9listen.listen_for_command()
    print("I heard: "+side)
    if "white" in side or "what" in side:
        player = chess.WHITE
        side = "white"
        break
    if "black" in side:
        player = chess.BLACK
        side = "black"
        break

speak("Affirmative. You are playing " + str(side))

'''

player = chess.WHITE

# MAIN GAME STATE
mem.storeState("chess",True)
while not board.is_game_over():
    print(board)
    if board.turn == player:
        # analyse the board
        if board.is_check(): speak(random_msg(check)) # announce check
        result = engine.analyse(board=board, limit=chess.engine.Limit(time=0.1),info=INFO_SCORE)
        score = result.score.pov(chess.WHITE)
        # prompt player for their move
        speak(random_msg(your_move))
        '''
        while True:
            move_str = k9listen.listen_for_command.lower()
            # move_str = input("Move?: ")
            print("I heard: "+move_str)
            move_str = move_str.translate({ord(c): None for c in string.whitespace})
            move_str = move_str.replace("to","2")
            if len(move_str)>4:
                move_str = move_str[0:2] + move_str[3:5]
            print("I converted it to: "+move_str)
            try:
                move = chess.Move.from_uci(move_str)
                if move in board.legal_moves:
                    break
            except:
                speak(random_msg(invalid_move))
        '''
    else:
        # determine the best move for K9 bot and analyse the board
        k9ears.think()
        result = engine.play(board=board, limit=chess.engine.Limit(time=5.0),info=INFO_SCORE)
        move = result.move
        score = result.info.score.pov(chess.WHITE)
        k9ears.stop()
    # Extract move context from board
    move_piece = pieces[board.piece_type_at(move.from_square)-1] 
    move_color = board.turn
    move_from = chess.SQUARE_NAMES[move.from_square]
    move_to = chess.SQUARE_NAMES[move.to_square]  
    if 'score' in context:
        old_score = context["score"]
        context.update(old_score = old_score)
    # Announce if piece is taken
    taken = board.piece_type_at(move.to_square)
    if taken is not None:
        if (board.turn == player):
            if (random.random() < (taken*0.2)):
                speak("You have taken my " + pieces[taken-1])
        else:
            speak("My " + move_piece + " " + random_msg(takes) + " your " + pieces[taken-1])
    # if no piece is taken, announce K9's move
    else:
        if (board.turn != player):
            speak(random_msg(instruction) + move_piece + " from " + move_from + " to " + move_to)
    context.update(player = player,
                   mv_color = move_color,
                   mv_from = move_from,
                   mv_to = move_to,
                   score = score,
                   piece = move_piece)
    # number = 3 and random 0.8
    if ((board.fullmove_number > 3) and (random.random()>0.7)): speak(get_phrase())
    board.push(move)
    print()

# END GAME STATE
engine.quit()
print(board)
if board.is_checkmate():
    if board.turn == player:
        speak("Checkmate - I have won")
    else:
        speak("Congratulations - you have won")
if board.is_stalemate(): message = "We have drawn through stalemate"
if board.is_insufficient_material(): message = "A draw is now inevitable due to insufficient material."
if board.is_seventyfive_moves(): message = "I am really bored.  We have drawn through repetition." 
if board.is_fivefold_repetition(): message= "The game is over, it has been drawn through repetition." 
speak(message)
speak("Thank you for a lovely game")
mem.storeState("chess",False)