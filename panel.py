import pyb

patterns = {
    "original": [[4],[5],[6],[8],[1],[10],[9],[12],[7],[11],[2],[3]],
    "colour": [[5,10,7,4],[1,9,2,8],[6,3,12],[11]],
    "diagonal" : [[9],[6],[3],[10],[7],[4],[11],[8],[12],[5],[2],[1]],
    "two": [[5,3],[9,8],[2,7],[6,12],[1,11],[10,4]],
    "three": [[1,10,8],[9,2,11],[5,7,4],[6,3,12]],
    "four": [[1,10,7,4],[9,2,11,8],[5,6,3,12]],
    "six": [[1,9,6,3,11,8],[5,2,10,7,4,12]],
    "red": [[5,10,7,4]],
    "green": [[1,9,2,8]],
    "blue": [[6,3,12]],
    "spiral": [[7],[6],[5],[9],[10],[11],[12],[8],[4],[3],[2],[1]],
    "chase_v": [[1],[5],[9],[10],[6],[2],[3],[7],[11],[12],[8],[4]],
    "chase_h": [[1],[2],[3],[4],[8],[7],[6],[5],[9],[10],[11],[12]],
    "cols" : [[1,5,9],[2,6,10],[3,7,11],[4,8,12]],
    "rows" : [[1,2,3,4],[5,6,7,8],[9,10,11,12]],
    "on": [[1,2,3,4,5,6,7,8,9,10,11,12]],
    "off": [[]]
}

speeds = {
    "fastest": 50,
    "fast"   : 100,
    "normal" : 200,
    "slow"   : 400,
    "slowest": 800
}

pins = ["Y1","Y2","Y3","Y4","Y5","Y6","Y7","Y8","X9","X10","X11","X12"]

def main():
    seq = patterns["original"]
    seq_len = len(seq)
    phase = 0
    wait = 150
    serial = pyb.USB_VCP()
    # leds = range(1,5)
    while True:
        # Turn off all lights
        for pin in pins:
            p = pyb.Pin(pin, Pin.OUT_PP)
            p.low()
            #pyb.LED(led).off()
        # Turn on all lights in this phase
        for pin in seq[phase]:
            p = pyb.Pin(pins[seq[phase][pin]], Pin.OUT_PP)
            p.high()
            #pyb.LED(led).on()
        phase += 1 # increment the phase
        # go back to phase zero if done
        if phase > seq_len -1: 
            phase = 0
        pyb.delay(wait)
        # check for instructions from Pi
        lines = serial.readlines()
        if lines:
            for line in lines:
                command = ""
                command = line.decode().strip()
                # if the command is a light
                # sequence then switch to that
                # one and reset phase
                if command in patterns:
                    seq = patterns[command]
                    seq_len = len(seq)
                    phase = 0
                # if the command is speed
                # related then change
                # wait time
                if command in speeds:
                    wait = int(speeds[command])
main()