from back_panel import BackLights
import time
k9lights = BackLights()
k9lights.tv_on([0,2,4,8,10])
while True:
    state = k9lights.get_switch_state()
    print(state)
    time.sleep(0.5)