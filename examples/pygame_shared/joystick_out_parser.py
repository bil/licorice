# this parser code brings data into the licorice system

joystick_axis[:] = [ (<double *>bufCurPtr)[0], (<double *>bufCurPtr)[1] ]

joystick_buttons[:] = [
  # TODO allow for {{config}} to be passed into parsers to simplify below
  bufCurPtr[128 + i] for i in range(joystick_buttons.size)
]
