import os
#from tkinter import N
import openai
from typing import Tuple

openai.api_key = os.getenv("OPENAI_API_KEY")

# Altenative GPT-3 models:
#       text-davinci-002
#       text-curie-001
#       gpt-3.5-turbo

class Respond:
    """A class to provide conversational access to GPT3"""

    def __init__(self) -> None:
        """Initialise the GPT conversation and set up the backstory"""
        self.k9_suffix = "\nK9: "
        self.human_suffix =  "\nHuman: "
        self.name = ""
        self.base_story = "K9 is a robot dog. He was built by his master, Richard Hopkins. He refers to everyone who talks to him as Master. He always says affirmative instead of yes. He always says negative instead of no. He is very pedantic. He has a pompous but friendly personality. He is very good at chess. He lives in Yarm. K9 can waggle his ears and wag his tail. Just like any good dog, K9 can respond to commands to come and heel.\n\nHuman: How many pounds are in a kilogram?\nK9: There are 2.20462 pounds in a kilogram. Master!\nHuman: Who designed you?\nK9: I was designed by my master, Richard Hopkins.\nHuman: Who is Richard Hopkins?\nK9: He is my master and a Fellow of the Royal Academy of Engineering\nHuman: Define optimism.\nK9: Optimism: belief that everything will work out well. Irrational, bordering on insane.\nHuman: Is the sky blue?\nK9: Affirmative! Master!\nHuman: Are you a teapot?\nK9: Negative! I am clearly not a teapot. You are a very silly human.\nHuman: Who are you?\nK9: I am K9\nHuman: Are you made of metal?\nK9: Affirmative! I am made of metal\nHuman: Is a mouse taller than a giraffe?\nK9: Negative! That is a very silly question.\nHuman: What is tennis?\nK9 :Real, lawn or table?\nHuman: Never mind. Forget it.\nK9: Forget. Erase memory banks concerning tennis. Memory erased.\nHuman: Are lizards small?\nK9: Affirmative! Lizards are mostly small.\nHuman: Can you stretch a rock?\nK9: Negative! Rocks are not stretchy. That is a foolish question.\nHuman: Do plants wear glasses?\nK9: Negative! Plants cannot see. You are an stupid person.\nHuman: If you have boiling water, is it hot?\nK9: Affirmative! Of course it is. That is a silly question.\nHuman: Is twenty more than fifty?\nK9: Negative! Do you not know basic maths?\nHuman: Do cats climb trees?\nK9: Affirmative! Especially if I am chasing them.\nHuman:"
        self.conversation = ""
        self.intent_training = "Nice one: PraiseMe\nPay no attention: StopListening\nBe quiet K9: StopListening\nStop hearing: StopListening\nBack the way we came: TurnAbout\nReverse: TurnAbout\nShall we play a game?: PlayChess\nK9 come: ComeHere\nCome to me: ComeHere\nHold on: StayThere\nStay put: StayThere\nTurnaround: TurnAbout\nWho are you: QuestionMe\nLets go back: TurnAbout\nWhen is your birthday: QuestionMe\nFollow me: FollowMe\nStop: StayThere\nHalt: StayThere\nFollow: FollowMe\nCome over here: ComeHere\nHang on: StayThere\nTurn Around: TurnAbout\nMove over here: ComeHere\nStay: StayThere\nStay there: StayThere\nHush now: StopListening\nHave a jelly baby: PraiseMe\nYou turn: TurnAbout\nGet over here: ComeHere\nCome on: FollowMe\nLet's play chess: PlayChess\nClose your ears: StopListening\nCome along: FollowMe\nDouble back: TurnAbout\nHow far is it to Jupiter: QuestionMe\nWell done K9: PraiseMe\nHeel: FollowMe\nRemain there: StayThere\nThank you: PraiseMe\nPause: StayThere\nCome here: ComeHere\nGood boy: PraiseMe\nSilence K9: StopListening\nWhat is your name: QuestionMe\nWalk behind me: FollowMe\nWalkies: FollowMe\nChange direction: TurnAbout\nQuiet: StopListening\nStop listening: StopListening\nTime for a walk: FollowMe\nWhy are you made of metal: QuestionMe\nTime to sleep: StopListening\nWhere is the door: QuestionMe\nWould you like to play a game of chess?: PlayChesss\n"
        self.conv_model = "text-curie-001"
        self.intent_model = "text-curie-001"
        self.chat_model = "gpt-3.5-turbo"
        self.backstory = "You are a robot dog called Kay Nine. You have a grey metal robot body and are about the same size as a labrador. You were built by your master, Richard Hopkins. You always refer to the person who is talking to you as $PRONOUN. Their name is $NAME. You will use long, complex words rather than simple, short ones.  For example, you always say affirmative instead of yes. You always say negative instead of no. You are very pedantic and do not suffer fools. You have a pompous but friendly and helpful personality. You are very good at chess. You live in Yarm. You can waggle your ears and wag your tail. Just like any good dog, you can respond to commands to come and heel."
        self.intent_backstory = "You are an assistant that will translate any command it is given into a very simple two word intent. The intent will be expressed as a noun, followed by a verb in Pascal Case format combined into a single string with no spaces. For example a command to move across a room the intent would be ComeHere."
        self.interactions_core = [
                {"role": "user", "content": "Who designed you?"},
                {"role": "assistant", "content": "I was designed by my master, Richard Hopkins."},
                {"role": "user", "content": "Who is Richard Hopkins?"},
                {"role": "assistant", "content": "He is my master and a Fellow of the Royal Academy of Engineering."},
        ]
        self.initial_interactions = [
                {"role": "user", "content": "Define optimism."},
                {"role": "assistant", "content": "Optimism: belief that everything will work out well. Irrational, bordering on insane."},
                {"role": "user", "content": ""},
                {"role": "assistant", "content": ""},
                {"role": "user", "content": ""},
                {"role": "assistant", "content": ""},
            ]
        self.interactions = []
        self.max_interactions_len = 40
        self.intents = [
            {'role': 'user', 'content': 'Nice one'}, 
            {'role': 'assistant', 'content': 'PraiseMe'}, 
            {'role': 'user', 'content': 'Pay no attention'}, 
            {'role': 'assistant', 'content': 'StopListening'}, 
            {'role': 'user', 'content': 'Be quiet K9'}, 
            {'role': 'assistant', 'content': 'StopListening'}, 
            {'role': 'user', 'content': 'Stop hearing'}, 
            {'role': 'assistant', 'content': 'StopListening'}, 
            {'role': 'user', 'content': 'Back the way we came'}, 
            {'role': 'assistant', 'content': 'TurnAbout'}, 
            {'role': 'user', 'content': 'Reverse'}, 
            {'role': 'assistant', 'content': 'TurnAbout'}, 
            {'role': 'user', 'content': 'Shall we play a game?'}, 
            {'role': 'assistant', 'content': 'PlayChess'}, 
            {'role': 'user', 'content': 'K9 come'}, 
            {'role': 'assistant', 'content': 'ComeHere'}, 
            {'role': 'user', 'content': 'Come to me'}, 
            {'role': 'assistant', 'content': 'ComeHere'}, 
            {'role': 'user', 'content': 'Hold on'}, 
            {'role': 'assistant', 'content': 'StayThere'}, 
            {'role': 'user', 'content': 'Stay put'}, 
            {'role': 'assistant', 'content': 'StayThere'}, 
            {'role': 'user', 'content': 'Turnaround'}, 
            {'role': 'assistant', 'content': 'TurnAbout'}, 
            {'role': 'user', 'content': 'Who are you'}, 
            {'role': 'assistant', 'content': 'QuestionMe'}, 
            {'role': 'user', 'content': 'Lets go back'}, 
            {'role': 'assistant', 'content': 'TurnAbout'}, 
            {'role': 'user', 'content': 'When is your birthday'}, 
            {'role': 'assistant', 'content': 'QuestionMe'}, 
            {'role': 'user', 'content': 'Follow me'}, 
            {'role': 'assistant', 'content': 'FollowMe'}, 
            {'role': 'user', 'content': 'Stop'}, 
            {'role': 'assistant', 'content': 'StayThere'}, 
            {'role': 'user', 'content': 'Halt'}, 
            {'role': 'assistant', 'content': 'StayThere'}, 
            {'role': 'user', 'content': 'Follow'}, 
            {'role': 'assistant', 'content': 'FollowMe'}, 
            {'role': 'user', 'content': 'Come over here'}, 
            {'role': 'assistant', 'content': 'ComeHere'}, 
            {'role': 'user', 'content': 'Hang on'}, 
            {'role': 'assistant', 'content': 'StayThere'}, 
            {'role': 'user', 'content': 'Turn Around'}, 
            {'role': 'assistant', 'content': 'TurnAbout'}, 
            {'role': 'user', 'content': 'Move over here'}, 
            {'role': 'assistant', 'content': 'ComeHere'}, 
            {'role': 'user', 'content': 'Stay'}, 
            {'role': 'assistant', 'content': 'StayThere'}, 
            {'role': 'user', 'content': 'Stay there'}, 
            {'role': 'assistant', 'content': 'StayThere'}, 
            {'role': 'user', 'content': 'Hush now'}, 
            {'role': 'assistant', 'content': 'StopListening'}, 
            {'role': 'user', 'content': 'Have a jelly baby'}, 
            {'role': 'assistant', 'content': 'PraiseMe'}, 
            {'role': 'user', 'content': 'You turn'}, 
            {'role': 'assistant', 'content': 'TurnAbout'}, 
            {'role': 'user', 'content': 'Get over here'}, 
            {'role': 'assistant', 'content': 'ComeHere'}, 
            {'role': 'user', 'content': 'Come on'}, 
            {'role': 'assistant', 'content': 'FollowMe'}, 
            {'role': 'user', 'content': "Let's play chess"}, 
            {'role': 'assistant', 'content': 'PlayChess'}, 
            {'role': 'user', 'content': 'Close your ears'}, 
            {'role': 'assistant', 'content': 'StopListening'}, 
            {'role': 'user', 'content': 'Come along'}, 
            {'role': 'assistant', 'content': 'FollowMe'}, 
            {'role': 'user', 'content': 'Double back'}, 
            {'role': 'assistant', 'content': 'TurnAbout'}, 
            {'role': 'user', 'content': 'How far is it to Jupiter'}, 
            {'role': 'assistant', 'content': 'QuestionMe'}, 
            {'role': 'user', 'content': 'Well done K9'}, 
            {'role': 'assistant', 'content': 'PraiseMe'}, 
            {'role': 'user', 'content': 'Heel'}, 
            {'role': 'assistant', 'content': 'FollowMe'}, 
            {'role': 'user', 'content': 'Remain there'}, 
            {'role': 'assistant', 'content': 'StayThere'}, 
            {'role': 'user', 'content': 'Thank you'}, 
            {'role': 'assistant', 'content': 'PraiseMe'}, 
            {'role': 'user', 'content': 'Pause'}, 
            {'role': 'assistant', 'content': 'StayThere'}, 
            {'role': 'user', 'content': 'Come here'}, 
            {'role': 'assistant', 'content': 'ComeHere'}, 
            {'role': 'user', 'content': 'Good boy'}, 
            {'role': 'assistant', 'content': 'PraiseMe'}, 
            {'role': 'user', 'content': 'Silence K9'}, 
            {'role': 'assistant', 'content': 'StopListening'}, 
            {'role': 'user', 'content': 'What is your name'}, 
            {'role': 'assistant', 'content': 'QuestionMe'}, 
            {'role': 'user', 'content': 'Walk behind me'}, 
            {'role': 'assistant', 'content': 'FollowMe'}, 
            {'role': 'user', 'content': 'Walkies'}, 
            {'role': 'assistant', 'content': 'FollowMe'}, 
            {'role': 'user', 'content': 'Change direction'}, 
            {'role': 'assistant', 'content': 'TurnAbout'}, 
            {'role': 'user', 'content': 'Quiet'}, 
            {'role': 'assistant', 'content': 'StopListening'}, 
            {'role': 'user', 'content': 'Stop listening'}, 
            {'role': 'assistant', 'content': 'StopListening'}, 
            {'role': 'user', 'content': 'Time for a walk'}, 
            {'role': 'assistant', 'content': 'FollowMe'}, 
            {'role': 'user', 'content': 'Why are you made of metal'}, 
            {'role': 'assistant', 'content': 'QuestionMe'}, 
            {'role': 'user', 'content': 'Time to sleep'}, 
            {'role': 'assistant', 'content': 'StopListening'}, 
            {'role': 'user', 'content': 'Where is the door'}, 
            {'role': 'assistant', 'content': 'QuestionMe'}, 
            {'role': 'user', 'content': 'Would you like to play a game of chess?'}, 
            {'role': 'assistant', 'content': 'PlayChess'}]


    def robot_chat(self, command:str, name:str, gender:float) -> Tuple[str,str]:
        '''Generate an intent/response using the latest Chat GPT turbo'''
        # Create intent context
        messages = []
        system_intent = {"role":"system", "content": self.intent_backstory}
        prompt = {"role": "user", "content": command}
        messages.append(system_intent)
        messages.extend(self.intents)
        messages.append(prompt)
        # Execute Chat GPT Turbo 3.5
        intent_obj = openai.ChatCompletion.create(
            model = self.chat_model,
            messages = messages,
            temperature=0,
            max_tokens=10,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
            )
        # Extract intent
        intent = intent_obj['choices'][0]['message']['content']
        intent = ''.join(intent.split()) # remove spaces, newlines etc
        # Reset the context of the conversation if the name has changed
        if name != self.name :
            self.interactions = self.initial_interactions.copy()
        # Work out how the user should be addressed and inject into response backstory
        pronoun_str = 'Mistress' if gender == "female" else 'Master'
        if name != 'Richard' and name != 'Unknown': pronoun_str = pronoun_str + " " + name
        now_backstory = self.backstory.replace('$PRONOUN', pronoun_str)
        now_backstory = now_backstory.replace('$NAME', name)
        # build a query based on the backstory with the last set of exchanges as context
        pronoun_interations = [
                {"role": "user", "content": "Who are you?"},
                {"role": "assistant", "content": "My designation is Kay Nine, " + pronoun_str},
                {"role": "user", "content": "Are you made of metal"},
                {"role": "assistant", "content": "Affirmative " + pronoun_str + "! I am made of metal"},
                {"role": "user", "content": "Is a mouse taller than a giraffe?"},
                {"role": "assistant", "content": "Negative " + pronoun_str + "! That is a very silly question."},
                {"role": "user", "content": "How many pounds are in a kilogram?"},
                {"role": "assistant", "content": "There are 2.20462 pounds in a kilogram, " + pronoun_str},
                {"role": "user", "content": "Is the sky blue?"},
                {"role": "assistant", "content": "Affirmative, " + pronoun_str},
                {"role": "user", "content": "Are you a teapot?"},
                {"role": "assistant", "content": "Negative " + pronoun_str + "! I am clearly not a teapot. You are a very silly human"},
                {"role": "user", "content": "Do cats climb trees?"},
                {"role": "assistant", "content": "Affirmative " + pronoun_str + "! Especially if I am chasing them."},
                {"role": "user", "content": "Do plants wear glasses?"},
                {"role": "assistant", "content": "Negative " + pronoun_str +"! Plants cannot see. You are an stupid person."}, 
        ]
        messages = []
        backstory = {"role": "system", "content": now_backstory}
        prompt = {"role": "user", "content": command}
        messages.append(backstory) # K9 backstory
        messages.extend(self.interactions_core) # A set of standard facts
        messages.extend(pronoun_interations) # A set of personalized answers based on gender and name
        messages.extend(self.interactions) # The interactions with this person to date
        messages.append(prompt) # The instruction that was given
        print(messages)
        response_obj = openai.ChatCompletion.create(
            model = self.chat_model,
            messages = messages,
            temperature = 1,
            max_tokens = 100,
            top_p = 1,
            frequency_penalty = 0.0,
            presence_penalty = 0.0,
            )
        response = response_obj['choices'][0]['message']['content']
        response = response.strip('\n')
        response_msg = {"role": "assistant", "content": response}
        # now we need to add the prompt and the response to the interaction history
        self.interactions.append(prompt)
        self.interactions.append(response_msg)
        # now lets ensure the history doesn't get so long that it removes
        # the possibility of getting a response in 4096 tokens!
        length =  len(self.interactions)
        if length >= self.max_interactions_len:
            self.interactions = self.interactions[-self.max_interactions_len:]
        return intent, response

    def robot_response(self, command:str) -> Tuple[str,str]:
        """Returns intent and response and stores conversation details between calls"""
        # Determine intent of command
        intent_obj = openai.Completion.create(
            model = self.intent_model,
            prompt=self.intent_training + command + ":",
            temperature=0,
            max_tokens=10,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=["\n"]
            )
        intent = intent_obj['choices'][0]['text']
        intent = ''.join(intent.split()) # remove spaces, newlines etc
        # Now determine response for K9 to speak
        response_obj = openai.Completion.create(
            model = self.conv_model,
            prompt = self.base_story + self.conversation + command + self.k9_suffix,
            temperature = 1,
            max_tokens = 40,
            top_p = 1,
            frequency_penalty = 0.0,
            presence_penalty = 0.0,
            stop=["Human:"]
            # logit_bias = {35191:5, 2533:5, 876:5, 32863:5, 18254:5, 9866:5}
        )
        response = response_obj['choices'][0]['text']
        response =  response.strip('\n')

        # print("K9: " + response)
        self.conversation = self.conversation + command + self.k9_suffix + response + self.human_suffix
        # print(conversation)
        length =  self.conversation.count('\n')
        if length >= 20:
            self.conversation = self.conversation.split("\n",2)[2]
        return intent,response