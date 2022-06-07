res = np.sum(
    [np.sin(2 * np.pi * freq * counter_interleaved) for freq in freqs], axis=0
)[:]
for i in range(res.size):
    if i % 2 == 0:  # 1 for left
        res[i] = 0
sine_wave[:] = res
counter_interleaved += timestep
