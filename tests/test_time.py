import sqlite3
import subprocess

import pytest

import licorice
from tests.utils import validate_model_output

NUM_TICKS = 10

clock_time_model = {
    "config": {
        "tick_len": 10000,
        "num_ticks": NUM_TICKS,
    },
    "signals": {
        "clock_time": {
            "shape": 1,
            "dtype": "double",
            "log": True,
        },
        "tick_num": {
            "shape": 1,
            "dtype": "uint64",
            "log": True,
        },
    },
    "modules": {
        "clock": {
            "language": "python",
            "out": ["clock_time", "tick_num"],
        },
        "logger": {
            "language": "python",
            "in": ["clock_time", "tick_num"],
            "out": {
                "name": "log_sqlite",
                "async": True,
                "args": {
                    "type": "disk",
                    "save_file": "./data"
                },
            },
        },
    },
}


def test_clock_time(capfd):
    # run LiCoRICE
    try:
        licorice.go(
            clock_time_model,
            confirm=True,
            working_path=f"{pytest.test_dir}/module_code",
        )
    except subprocess.CalledProcessError:
        pass

    validate_model_output(capfd, NUM_TICKS)

    # read values written to sqlite database
    conn = sqlite3.connect(
        f"{pytest.test_dir}/module_code/run.lico/out/data_0000.db"
    )
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(signals);")
    col_names = [val[1] for val in cur.fetchall()]

    clock_time_idx = col_names.index("r_f8_clock_time")
    time_num_idx = col_names.index("r_u8_tick_num")
    cur.execute("SELECT * FROM signals;")
    values = [value for value in cur.fetchall()]

    expected_diff = .01
    tolerance = .001

    for i in range(1, len(values)):
        # tick times should be sequential
        assert values[i][time_num_idx] - values[i - 1][time_num_idx] == 1
        # clock times should be 10ms apart (1ms jitter tolerance)
        assert (
            abs(
                (values[i][clock_time_idx] - values[i - 1][clock_time_idx]) -
                expected_diff
            ) < tolerance
        )
