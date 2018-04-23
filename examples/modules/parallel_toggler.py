if toggle_state == 0:
    toggle_state = 1
    out_sigs['parallel_sink_input'][0] = 0b10000000 # set pin 9 of parallel port to 1
else:
    toggle_state = 0
    out_sigs['parallel_sink_input'][0] = 0b00000000
