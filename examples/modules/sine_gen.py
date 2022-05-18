sine_wave[:] = np.sum([np.sin(2 * np.pi * freq * counter_interleaved) for freq in freqs], axis=0)[:]
counter_interleaved += timestep
