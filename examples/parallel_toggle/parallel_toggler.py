# Toggle pin 9 of the parallel port every two seconds

if pNumTicks[0] % 1000 == 0:
    parallel_in_val = parallel_in >> 7 # get pin 9 value
    print(f"Parallel port input value at time {pNumTicks[0]//1000}s: {parallel_in_val}", flush=True)
    
if pNumTicks[0] % 2000 == 0:  # pNumTicks[0] is value of the current timer tick
    if toggle_state == 0:
        toggle_state = 1
    else:
        toggle_state = 0
    print(f"Toggled state to: {toggle_state}", flush=True)

if toggle_state == 1: 
    # set pin 9 of parallel port to 1
    parallel_out[:] = 0b10000000
else:
    parallel_out[:] = 0b00000000
    