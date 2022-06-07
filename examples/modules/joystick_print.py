# this is a print module for the joystick
# prints every 15ms

if not pNumTicks[0] % 15:  # pNumTicks[0] is the tick counter
    print(((joystick_axis[0], joystick_axis[1]), joystick_buttons[:]))
