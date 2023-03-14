import math
import os

import yaml

import licorice


def round_inv(x):
    if (x - int(x) < 0.5):
        return int(math.ceil(x))
    else:
        return int(math.floor(x))


working_path = os.path.dirname(os.path.realpath(__file__))

with open(f"{working_path}/audio_capture.yaml", "r") as f:
    model_dict = yaml.safe_load(f)

# read vars from model
in_sig = model_dict["modules"]["audio_in"]["in"]
in_rate = in_sig["args"]["pcm"]["rate"]
out_sig = model_dict["modules"]["audio_out"]["out"]
out_rate = out_sig["args"]["pcm"]["rate"]
tick_len = model_dict["config"]["tick_len"]

# overrides
tick_len = 10000
in_rate = 48000
out_rate = 48000

# set new vars
sig_len = int(in_rate / (1.e6 / tick_len))

# period and buffer defaults
in_period_time = tick_len
in_buffer_time = 0
out_period_time = tick_len
out_buffer_time = 0

# period and buffer overrides
# in_period_num = 128
# in_period_time = round_inv(1.e6 * in_period_num / out_rate)
# out_period_num = 256
# out_buffer_num = 384
# out_period_time = round_inv(1.e6 * out_period_num / out_rate)
# out_buffer_time = round_inv(1.e6 * out_buffer_num / out_rate)

# update model dict
model_dict["config"]["tick_len"] = tick_len
signals = model_dict["signals"]
for sig, _ in signals.items():
    signals[sig]["shape"] = f"({sig_len}, )"
in_sig["args"]["pcm"]["rate"] = in_rate
in_sig["args"]["pcm"]["period_time"] = in_period_time
in_sig["args"]["pcm"]["buffer_time"] = in_buffer_time
in_sig["schema"]["data"]["size"] = sig_len
out_sig["args"]["pcm"]["rate"] = out_rate
out_sig["args"]["pcm"]["period_time"] = out_period_time
out_sig["args"]["pcm"]["buffer_time"] = out_buffer_time
out_sig["schema"]["data"]["size"] = sig_len

print(model_dict)

licorice.go(model_dict, confirm=True, working_path=working_path, realtime=True)
