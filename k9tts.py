from subprocess import Popen

# These values control K9s voice
SPEED_DEFAULT = 150
SPEED_DOWN = 125
AMP_UP = 100
AMP_DEFAULT = 50
AMP_DOWN = 25
PITCH_DEFAULT = 99
PITCH_DOWN = 89
SOX_VOL_UP = 25
SOX_VOL_DEFAULT = 20
SOX_VOL_DOWN = 15
SOX_PITCH_UP = 100
SOX_PITCH_DEFAULT = 0
SOX_PITCH_DOWN = -100

def speak(speech):
        '''
        Break speech up into clauses using | and speak each one with
        various pitches, volumes and distortions
        to make the voice more John Leeson like
        > will raise the pitch and amplitude
        < will lower it
        '''
        
        print('speech:', speech)
        speaking = None
        clauses = speech.split("|")
        for clause in clauses:
            if clause and not clause.isspace():
                if clause[:1] == ">":
                    clause = clause[1:]
                    pitch = PITCH_DEFAULT
                    speed = SPEED_DOWN
                    amplitude = AMP_UP
                    sox_vol = SOX_VOL_UP
                    sox_pitch = SOX_PITCH_UP
                elif clause[:1] == "<":
                    clause = clause[1:]
                    pitch = PITCH_DOWN
                    speed = SPEED_DOWN
                    amplitude = AMP_DOWN
                    sox_vol = SOX_VOL_DOWN
                    sox_pitch = SOX_PITCH_DOWN
                else:
                    pitch = PITCH_DEFAULT
                    speed = SPEED_DEFAULT
                    amplitude = AMP_DEFAULT
                    sox_vol = SOX_VOL_DEFAULT
                    sox_pitch = SOX_PITCH_DEFAULT
                #cmd = "espeak -v en-rp '%s' -p %s -s %s -a %s -z" % (clause, pitch, speed, amplitude)
                cmd = ['espeak','-v','en-rp',str(clause),'-p',str(pitch),'-s',str(speed),'-a',str(amplitude)]
                speaking = Popen(cmd)
                Popen.terminate(speaking)