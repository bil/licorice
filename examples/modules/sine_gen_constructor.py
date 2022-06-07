sampling_rate = 44100 # TODO make this available from config
timestep = .1
freqs = np.array([261.63,  329.63, 392.]) * 2 # c major chord
# freqs = [440.]
counter = np.arange(timestep * sampling_rate).astype(np.float64) / sampling_rate
counter_interleaved = np.array(list(zip(counter, counter))).flatten()
