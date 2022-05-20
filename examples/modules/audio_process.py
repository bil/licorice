# play noise
# audio_signal_sink = np.random.random(audio_signal_source.shape)

res = audio_signal_source[:]

# weird noise
# max_val = np.max(res)
# res = (res / max_val) * np.iinfo(np.int16).max / 2

# distortion
if enable_distortion:
    clip_val = np.max(res) / clip_ratio
    np.clip(res, -1. * clip_val, clip_val, res)

# filtering

# lowpass
if enable_lowpass:
    res, low_z = signal.lfilter(
        low_filter_params[0],
        low_filter_params[1],
        res,
        zi=low_z
    )

# highpass
if enable_highpass:
    res, high_z = signal.lfilter(
        high_filter_params[0],
        high_filter_params[1],
        res,
        zi=high_z
    )

# channel select
# for i in range(res.size):
#     if i%2 == 1: # 1 for left
#         res[i] = 0

# audio_signal_sink[:] = np.zeros(res.shape)
audio_signal_sink[:] = res
