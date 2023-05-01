from back_panel import BackLights
bp = BackLights()
original = bp.get_switch_state()
while True:
        new = bp.get_switch_state()
        for i,state in enumerate(new):
                if state != original[i]:
                        print("Button",i,"pressed.")