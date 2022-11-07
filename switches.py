from machine import Pin

debounce_time = 10

# Empty list of switchh states
switch_states = []

# Create list of switch pins
switch_labels = ["X1","X2","X3","X4","X5","X6","X7","X8","Y9","Y10","Y11","Y12"]
switches = []
for switch in switch_labels:
    switches.append(Pin(switch, Pin.IN, Pin.PULL_DOWN))

def debounced_switches():
    global switch_states
    # Record the state of all switches as true or false
    switch_values=[]
    for switch in switches:
        switch_values.append(bool(switch.value()))
    # Append the latest state of all switches to
    # the state list
    switch_states.append(switch_values)
    # Trim the number of states to match
    # the debounce timer by popping off
    # the top of the list if needed
    if len(switch_states) > debounce_time:
        switch_states.pop(0)
    # Transpose the state x switch 2D array so that each
    # switch is a row with its own history.  Then 
    # logically AND the history of each switch
    # Switches with all True, will be True, every other
    # state (including any bounciness) will be False
    debounced = [all(l) for l in zip(*switch_states)]
    return debounced

while True:
    debounced = debounced_switches()
    print(debounced)