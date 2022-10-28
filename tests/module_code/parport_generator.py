if pNumTicks[0] % 2 == 0:
    gen_signal_1 = (gen_signal_1 + 1) % 2
else:
    gen_signal_2 = (gen_signal_2 + 1) % 2

signal_1[:] = gen_signal_1
signal_2[:] = gen_signal_2
