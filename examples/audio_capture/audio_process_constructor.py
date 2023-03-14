import sys
import time

import pygame
import pygame.midi
from pedalboard import (
    Bitcrush,
    Distortion,
    Gain,
    Pedalboard,
    Phaser,
    PitchShift,
    Reverb,
)
from scipy import signal

np.set_printoptions(threshold=sys.maxsize)

pygame.midi.init()
print(flush=True)

midi_avail = True
if pygame.midi.get_count() < 3:
    midi_avail = False

if midi_avail:
    try:
        midi_input_device = 5
        mIn = pygame.midi.Input(midi_input_device)
    except Exception as e:
        print(e)
        midi_avail = False

if not midi_avail:
    print("External MIDI board not found! Disabling FX.\n", flush=True)

sample_rate = 44100

# gain
gain_min = -30
gain_max = 5
gain_boards = [
    Pedalboard([Gain(gain_db=(gain_max - gain_min) * (i / 127.0) + gain_min)])
    for i in range(128)
]
# gain_board = gain_boards[len(gain_boards) // 2]
gain_board = gain_boards[len(gain_boards)-1]

# distortion
clip_ratio = 0.2
# distortion_board = Pedalboard([Distortion()])

# reverb
reverb_board = Pedalboard([Reverb(room_size=0.5)])

# phaser
phaser_boards = [
    Pedalboard(
        [Phaser(rate_hz=i + 1, feedback=0.2, centre_frequency_hz=800.0)]
    )
    for i in range(128)
]
phaser_board = phaser_boards[64]

# bitcrush
bitcrush_board = Pedalboard([Bitcrush(bit_depth=8)])

# ptich shift
pitch_shift_min = -12
pitch_shift_max = 12
pitch_shift_boards = [
    Pedalboard(
        [
            PitchShift(
                semitones=(pitch_shift_max - pitch_shift_min) * (i / 127.0)
                + pitch_shift_min
            )
        ]
    )
    for i in range(128)
]
pitch_shift_board = pitch_shift_boards[64]

# lowpass filter
low_pass_min = 60
low_pass_max = 5000
low_filter_params_list = []
for i in range(128):
    lp_val = (low_pass_max - low_pass_min) * (i / 127.0) + low_pass_min
    low_filter_params_list.append(
        signal.butter(3, lp_val, "low", fs=sample_rate)
    )
low_filter_params = low_filter_params_list[64]
low_z = signal.lfilter_zi(*low_filter_params)


# highpass filter
high_pass_min = 60
high_pass_max = 5000
high_filter_params_list = []
for i in range(128):
    lp_val = (high_pass_max - high_pass_min) * (i / 127.0) + high_pass_min
    high_filter_params_list.append(
        signal.butter(3, lp_val, "high", fs=sample_rate)
    )
high_filter_params = high_filter_params_list[64]
high_z = signal.lfilter_zi(*high_filter_params)

enable_distortion = False
enable_bitcrush = False
enable_pitch_shift = False
enable_reverb = False
enable_phaser = False
enable_lowpass = False
enable_highpass = False
power_off = False
channel_select = -1
