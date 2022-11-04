import pyb
patterns = {
    "one": [[1],[3],[2],[4]],
    "two": [[1,2],[2,3],[3,4],[4,1]],
    "three" : [[1,2,3],[2,3,4],[3,4,1],[4,1,2]],
    "chase": [[1],[2],[3],[4],[3],[2]]
}
pins = ["DUMMY","Y1","Y2","Y3","Y4","Y5","Y6","Y7","Y8","X9","X10","X11","X12"]
def main():
    seq = patterns["one"]
    seq_len = len(seq)
    phase = 0
    wait = 1000
    serial = pyb.USB_VCP()
    leds = range(1,5)
    while True:
        for led in leds:
            pyb.LED(led).off()
        for led in seq[phase]:
            pyb.LED(led).on()
        phase += 1
        if phase > seq_len -1:
            phase = 0
        pyb.delay(wait)
        lines = serial.readlines()
        if lines:
            for line in lines:
                command = ""
                command = line.decode().strip()
                if command in patterns:
                    seq = patterns[command]
                    seq_len = len(seq)
                    phase = 0
                # why isn't this working?!?!?
                elif "fast" in command:
                    wait = int(wait / 2)
                elif "slow" in command:
                    wait = int(wait * 2)

main()