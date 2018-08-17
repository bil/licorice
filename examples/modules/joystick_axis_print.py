# this is a print module for the joystick
# prints every 15ms

if not pNumTicks[0] % 15 : # pNumTicks[0] is the tick counter
  print( (joystick_axis_out[0], joystick_axis_out[1]) )
