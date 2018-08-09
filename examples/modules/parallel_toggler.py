# Toggle pin 9 of the parallel port every two seconds

if counter < 2000 :
    counter += 1
else:
    counter = 0

    if toggle_state == 0:
        toggle_state = 1
        out_sigs['parallel_out'][0] = 0b10000000 # set pin 9 of parallel port to 1
    else:
        toggle_state = 0
        out_sigs['parallel_out'][0] = 0b00000000
