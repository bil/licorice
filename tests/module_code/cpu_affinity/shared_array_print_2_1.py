diff = out_1_1BufVars[1] - out_1_1BufVars[0]
if diff:
    for i in range(diff):
        # out_2
        print(f"shared_array_print_output: { out_1_1[i] }", flush=True)
