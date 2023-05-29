from back_panel import BackLights
import time
k9lights = BackLights()
turn_on_lights = [1,2,3,5,12]
while True:
    state = k9lights.get_switch_state()
    print(state)
    time.sleep(0.5)