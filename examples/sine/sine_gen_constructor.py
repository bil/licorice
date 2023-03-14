# sampling_rate = 48000  # TODO make this available from config
sampling_rate = {{config["config"]["sampling_rate"]}}
timestep = 0.1
freqs = np.array([261.63, 329.63, 392.0]) * 2  # c major chord
# freqs = [440.]
counter = (
    np.arange(timestep * sampling_rate).astype(np.float64) / sampling_rate
)
counter_interleaved = np.array(list(zip(counter, counter))).flatten()

stereo_out = (True, False)  # left/right
