from scipy import signal

# distortion
clip_ratio = 1.1

# lowpass filter
low_filter_params = signal.butter(3, 1000., 'low', fs=48000)
low_z = signal.lfilter_zi(*low_filter_params)

# highpass filter
high_filter_params = signal.butter(3, 100., 'high', fs=48000)
high_z = signal.lfilter_zi(*high_filter_params)

enable_distortion = True
enable_lowpass = True
enable_highpass = False
