import sqlite3
import subprocess

import pytest

import licorice
from tests.utils import validate_model_output

NUM_TICKS = 10

clock_monotonic_model = {
    "config": {
        "tick_len": 10000,
        "num_ticks": NUM_TICKS,
    },
    "modules": {
        "logger": {
            "language": "python",
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


def test_clock_monotonic(capfd):
    # run LiCoRICE
    try:
        licorice.go(
            clock_monotonic_model,
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
    cur.execute("PRAGMA table_info(tick);")
    col_names = [val[1] for val in cur.fetchall()]

    time_tick_idx = col_names.index("time_tick")
    time_monotonic_raw_idx = col_names.index("time_monotonic_raw")
    time_monotonic_idx = col_names.index("time_monotonic")
    time_realtime_idx = col_names.index("time_realtime")
    cur.execute("SELECT * FROM tick;")
    values = [value for value in cur.fetchall()]

    # in nanoseconds
    expected_diff = 1e7
    tolerance = 1e6

    for i in range(1, len(values)):
        # tick times should be sequential
        assert values[i][time_tick_idx] - values[i - 1][time_tick_idx] == 1
        # clock times should be 10ms apart (1ms jitter tolerance)
        assert (
            abs(
                (
                    values[i][time_monotonic_raw_idx] -
                    values[i - 1][time_monotonic_raw_idx]
                ) -
                expected_diff
            ) < tolerance
        )

        assert (
            abs(
                (
                    values[i][time_monotonic_idx] -
                    values[i - 1][time_monotonic_idx]
                ) -
                expected_diff
            ) < tolerance
        )

        assert (
            abs(
                (
                    values[i][time_realtime_idx] -
                    values[i - 1][time_realtime_idx]
                ) -
                expected_diff
            ) < tolerance
        )
