# play noise
# audio_signal_sink = np.random.random(audio_signal_source.shape)

# print(f"bv0: {audio_signal_sourceBufVars[0]}, bv1: {audio_signal_sourceBufVars[1]}", flush=True)
# print(flush=True)
if midi_avail:
    while mIn.poll() :
        event = mIn.read(1)[0]
        ev_data = event[0]
        # print(event, flush=True)

        area = ev_data[0]
        control = ev_data[1] #which button
        value = ev_data[2] #value

        if area == 153: # pad pressed
            if control == 36: # pad 1
                enable_lowpass = not enable_lowpass
                print(f"lowpass: {enable_lowpass}", flush=True)
            if control == 37: # pad 2
                enable_highpass = not enable_highpass
                print(f"highpass: {enable_highpass}", flush=True)
            if control == 38: # pad 3
                enable_distortion = not enable_distortion
                print(f"distortion: {enable_distortion}", flush=True)
            if control == 39: # pad 4
                enable_phaser = not enable_phaser
                print(f"phaser: {enable_phaser}", flush=True)
            if control == 40: # pad 5
                enable_pitch_shift = not enable_pitch_shift
                print(f"pitch_shift: {enable_pitch_shift}", flush=True)
            if control == 41: # pad 6
                channel_select += 1
                if channel_select == 2:
                    channel_select = -1
                print(f"channel_select: {channel_select}", flush=True)
            if control == 42: # pad 7
                enable_reverb = not enable_reverb
                print(f"reverb: {enable_reverb}", flush=True)
            if control == 43: # pad 5
                enable_bitcrush = not enable_bitcrush
                print(f"bitcrush: {enable_bitcrush}", flush=True)
            if control == 51: # pad 16
                power_off = not power_off
                print(f"power_off: {power_off}", flush=True)

        if area == 176: # knob turned
            if control == 3: # knob 1
                low_filter_params = low_filter_params_list[value]
                print(f"lowpass cutoff: {(low_pass_max - low_pass_min) * (value / 127.) + low_pass_min}", flush=True)

            if control == 9: # knob 2
                high_filter_params = high_filter_params_list[value]
                print(f"highpass cutoff: {(high_pass_max - high_pass_min) * (value / 127.) + high_pass_min}", flush=True)


            if control == 12: # knob 3
                clip_ratio = 0.85 * (value / 127.) + 0.1
                print(f"distortion clip: {clip_ratio}", flush=True)

            if control == 13: # knob 4
                phaser_board = phaser_boards[value]
                print(f"phaser rate: {value+1}", flush=True)

            if control == 14: # knob 5
                pitch_shift_board = pitch_shift_boards[value]
                print(f"pitch_shift value: {(pitch_shift_max - pitch_shift_min) * (value / 127.) + pitch_shift_min }", flush=True)

            if control == 15: # knob 6
                gain_board = gain_boards[value]
                print(f"gain: {(gain_max - gain_min) * (value / 127.) + gain_min}db", flush=True)


res = audio_signal_source[:]
res = res[::2]
# print(res, flush=True)
# print(np.count_nonzero(res), flush=True)

# weird noise
# max_val = np.max(res)
# res = (res / max_val) * np.iinfo(np.int16).max / 2

# gain
res = gain_board(res, sample_rate)

# distortion
if enable_distortion:
    mean = int(np.mean(res))
    res -= mean
    clip_val = np.max(res) * clip_ratio
    np.clip(res, -1. * clip_val, clip_val, res)
    res += mean
    # res = distortion_board(res[:].astype(np.float32), sample_rate) 

# reverb
if enable_reverb:
    res = reverb_board(res, sample_rate)

# phaser
if enable_phaser:
    res = phaser_board(res, sample_rate)

# bitcrush
if enable_bitcrush:
    res = bitcrush_board(res, sample_rate)

if enable_pitch_shift:
    res = pitch_shift_board(res, sample_rate)

# filtering

# lowpass
if enable_lowpass:
    res, low_z = signal.lfilter(
        low_filter_params[0], low_filter_params[1], res, zi=low_z
    )

# highpass
if enable_highpass:
    res, high_z = signal.lfilter(
        high_filter_params[0], high_filter_params[1], res, zi=high_z
    )

# channel select
if channel_select >= 0:
    for i in range(res.size):
        if i % 2 == channel_select: # 0 for right; 1 for left
            res[i] = 0

# poweroff
if power_off:
    res = np.zeros(res.shape)


# res = np.random.random(res.shape) * 1000
# res = np.zeros(res.shape)
audio_signal_sink[:] = res
# audio_signal_sink[:] = audio_signal_source[:]

# print(res.shape, flush=True)
# print(np.count_nonzero(res), flush=True)
# print(res[:], flush=True)
