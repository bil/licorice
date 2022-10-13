# this is a print module for the joystick
# prints every 15ms

if not pNumTicks[0] % 10:  # pNumTicks[0] is the tick counter
  # synchronous
  # print(((joystick_axis[0], joystick_axis[1]), joystick_buttons), flush=True)

  # async or sync
  # axis = np.mean(joystick_axis, axis=0) 
  # buttons = np.clip(np.sum(joystick_buttons, axis=0), None, 1)


  ja = joystick_axisRaw[joystick_axisBufVars[8]:joystick_axisBufVars[9]]
  jb = joystick_buttonsRaw[joystick_buttonsBufVars[8]:joystick_buttonsBufVars[9]]
  axis = np.mean(ja, axis=0) 
  buttons = np.clip(np.sum(jb, axis=0), None, 1)

  print(((axis[0], axis[1]), buttons), flush=True)
