import time
from back_panel import BackLights
bp = BackLights()
bp.cmd("computer")
original = bp.get_switch_state()
print("original:",str(original))
while True:
        time.sleep(0.5)
        new = bp.get_switch_state()
        print("new     :",str(new))
        for i,state in enumerate(new):
                if state != original[i]:
                        print("Button",i,"pressed.")