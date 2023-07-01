diff = uint64_signalBufVars[1] - uint64_signalBufVars[0]
if diff:
    for i in range(diff):
        print(f"shared_array_print_output: { uint64_signal[i] }", flush=True)
