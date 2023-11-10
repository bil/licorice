if pNumTicks[0] % ({{out_signal["args"]["skip_ticks"]}} + 1) == 0:
    print("printer: ", countRaw[countBufVars[0]:countBufVars[1]], flush=True)
    outBuf[0] = count[:]
    outBufLen = 1
else:
    outBufLen = 0
