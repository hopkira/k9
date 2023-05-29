from back_panel import BackLights
import time
k9lights = BackLights()
turn_on_lights = [1,2,3,5,12]
k9lights.turn_on(turn_on_lights)
while True:
    state = k9lights.get_switch_state()
    print(state)
    time.sleep(0.5)