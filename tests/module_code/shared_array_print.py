diff = {{in_signals.keys()|first}}BufVars[1] - {{in_signals.keys()|first}}BufVars[0]
if diff:
    print("shared_array_print_diff: ", diff, flush=True)
    for i in range(diff):
        print(f"shared_array_print_output: { {{in_signals.keys()|first}}[i] }", flush=True)
