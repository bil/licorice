# this parser code brings data into the licorice system
joystick_axis[:] = [ (<double *>inBuf)[0], (<double *>inBuf)[1] ]

joystick_buttons[:] = [
  # TODO allow for { { config } } to be passed into parsers to simplify below
  (<uint8_t *>inBuf)[128 + i] for i in range(joystick_buttons.size)
]
