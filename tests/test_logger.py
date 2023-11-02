import copy
import math
import sqlite3
from collections import OrderedDict

import msgpack
import numpy as np
import pytest
import SharedArray as sa

import licorice
from licorice.templates.module_utils import create_shared_array
from tests.utils import TIME_COLNAMES, validate_model_output

NUM_TICKS = 100
TICK_TABLE_NAME = "tick"

logger_model_template = {
    "config": {
        "tick_len": 10000,
        "num_ticks": NUM_TICKS,
    },
    "signals": {},
    "modules": {
        "signal_generator": {
            "language": "python",
            "constructor": True,
            "out": [],
        },
        "logger": {
            "language": "python",
            "in": [],
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

TEST_DTYPES = [
    "int8",
    "int16",
    "int32",
    "int64",
    "uint8",
    "uint16",
    "uint32",
    "uint64",
    "float32",
    "float64",
]


def get_expected_list(num_ticks, dtype, seed=None):
    if seed is None:
        seed = dtype(1)

    expected_list = []
    for i in range(num_ticks):
        expected_list.append(seed + (i % 100))
    return np.array(expected_list)


def snapshot_sql_output(cur, snapshot):
    cur.execute(f"PRAGMA table_info({TICK_TABLE_NAME});")
    col_names = [val[1] for val in cur.fetchall()]
    # don't snapshot nanosecond timers
    for n in TIME_COLNAMES[1:]:
        col_names.remove(n)

    cur.execute(f"SELECT {' ,'.join(col_names)} FROM {TICK_TABLE_NAME};")

    col_vals = [[] for _ in col_names]
    for row in cur.fetchall():
        for i in range(len(col_names)):
            val = row[i]
            if col_names[i][0] == "m":
                # TODO format msgpack signals with correct shape
                val = msgpack.unpackb(val)
            col_vals[i].append(val)

    table_dict = OrderedDict(sorted(dict(zip(col_names, col_vals)).items()))
    assert table_dict == snapshot


# test logging one signal:
@pytest.mark.parametrize("enable", [True, False])
def test_single_signal(enable, capfd, snapshot):
    sig_type = "uint32"
    sig_name = f"{sig_type}_signal"

    # create LiCoRICE model dict
    logger_model = copy.deepcopy(logger_model_template)
    logger_model["config"]["num_ticks"] = NUM_TICKS
    logger_model["signals"] = {
        sig_name: {
            "shape": 1,
            "dtype": sig_type,
            "log": {"enable": enable},
        }
    }
    signal_list = [sig_name]
    logger_model["modules"]["signal_generator"]["out"] = signal_list
    logger_model["modules"]["logger"]["in"] = signal_list

    # run LiCoRICE
    licorice.go(
        logger_model,
        confirm=True,
        working_path=f"{pytest.test_dir}/module_code",
    )

    validate_model_output(capfd, NUM_TICKS)

    # read values written to sqlite database
    conn = sqlite3.connect(
        f"{pytest.test_dir}/module_code/run.lico/out/data_0000.db"
    )
    cur = conn.cursor()
    if enable:
        snapshot_sql_output(cur, snapshot)

    else:
        cur.execute('SELECT name FROM sqlite_master WHERE type = "table"')
        results = cur.fetchall()
        assert len(results) == 1  # tick table always created


def test_vector(capfd, snapshot):
    vector_shape = 10
    dtype_str = "int32"

    # create LiCoRICE model dict
    logger_model = copy.deepcopy(logger_model_template)
    logger_model["signals"] = {
        "vector_signal": {
            "shape": vector_shape,
            "dtype": dtype_str,
            "log": {"type": "vector"},
        }
    }
    signal_list = ["vector_signal"]
    logger_model["modules"]["signal_generator"]["out"] = signal_list
    logger_model["modules"]["logger"]["in"] = signal_list

    # run LiCoRICE
    licorice.go(
        logger_model,
        confirm=True,
        working_path=f"{pytest.test_dir}/module_code",
    )

    validate_model_output(capfd, NUM_TICKS)

    # read values written to sqlite database
    conn = sqlite3.connect(
        f"{pytest.test_dir}/module_code/run.lico/out/data_0000.db"
    )
    cur = conn.cursor()

    snapshot_sql_output(cur, snapshot)


def test_msgpack(capfd, snapshot):
    matrix_shape = (4, 4)
    dtype_str = "float32"

    # create LiCoRICE model dict
    logger_model = copy.deepcopy(logger_model_template)
    logger_model["signals"] = {
        "matrix_signal": {
            "shape": matrix_shape,
            "dtype": dtype_str,
            "log": True,
        }
    }
    signal_list = ["matrix_signal"]
    logger_model["modules"]["signal_generator"]["out"] = signal_list
    logger_model["modules"]["logger"]["in"] = signal_list

    # run LiCoRICE
    licorice.go(
        logger_model,
        confirm=True,
        working_path=f"{pytest.test_dir}/module_code",
    )

    validate_model_output(capfd, NUM_TICKS)

    # read values written to sqlite database
    conn = sqlite3.connect(
        f"{pytest.test_dir}/module_code/run.lico/out/data_0000.db"
    )
    cur = conn.cursor()

    snapshot_sql_output(cur, snapshot)


@pytest.mark.parametrize("enable", [True, False])
def test_multi_signal(enable, capfd):
    signals_dict = {}
    signal_list = []
    dict_vals = [
        ("scalar", 1, {"enable": True}),
        ("vector", 5, {"enable": enable, "type": "vector"}),
        ("matrix", (2, 2), {"enable": enable}),
    ]
    for dtype in TEST_DTYPES:
        for name, shape, log_args in dict_vals:
            sig_name = f"{name}_{dtype}_signal"
            signals_dict[sig_name] = {
                "shape": shape,
                "dtype": dtype,
            }
            signals_dict[sig_name]["log"] = log_args
            signal_list.append(sig_name)

    # create LiCoRICE model dict
    logger_model = copy.deepcopy(logger_model_template)
    logger_model["signals"] = signals_dict
    logger_model["modules"]["signal_generator"]["out"] = signal_list
    logger_model["modules"]["logger"]["in"] = signal_list

    # run LiCoRICE
    licorice.go(
        logger_model,
        confirm=True,
        working_path=f"{pytest.test_dir}/module_code",
    )

    validate_model_output(capfd, NUM_TICKS)

    # read values written to sqlite database
    conn = sqlite3.connect(
        f"{pytest.test_dir}/module_code/run.lico/out/data_0000.db"
    )
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({TICK_TABLE_NAME});")
    col_names = [val[1] for val in cur.fetchall()]
    for n in TIME_COLNAMES:
        col_names.remove(n)
    cur.execute(f"SELECT {','.join(col_names)} FROM {TICK_TABLE_NAME};")
    values = cur.fetchall()
    assert len(values) == NUM_TICKS
    new_values = []
    for value in values:
        new_values.append(
            [
                np.array(msgpack.unpackb(val)).reshape(dict_vals[2][1])
                if type(val) is bytes
                else val
                for val in value
            ]
        )
    values = np.array(new_values)

    seed = []
    for name in col_names:
        dtype = np.dtype(name.split("_")[1]).type
        if name.split("_")[0] == "m":
            seed.append(np.array(np.ones(dict_vals[2][1], dtype=dtype)))
        else:
            seed.append(dtype(1))
    seed = np.array(seed)
    expected_list = get_expected_list(NUM_TICKS, None, seed=seed)

    if not enable:
        assert (
            len(col_names) == len(TEST_DTYPES) and
            all(map(lambda x: "scalar" in x, col_names))
        )

    for i in range(len(values)):
        for j in range(len(values[i])):
            expected = expected_list[i][j]
            if expected.dtype.char in np.typecodes["AllFloat"]:
                assert np.allclose(expected, values[i][j])
            else:
                assert np.array_equal(expected, values[i][j])

    # TODO snapshot this result?


def test_suffixes(capfd):
    vector_shape = 3
    dtype = np.int64
    dtype_str = "int64"
    suffixes = ["x", "y", "z"]

    # create LiCoRICE model dict
    logger_model = copy.deepcopy(logger_model_template)
    logger_model["signals"] = {
        "vector_signal": {
            "shape": vector_shape,
            "dtype": dtype_str,
            "log": {"type": "vector", "suffixes": suffixes},
        }
    }
    signal_list = ["vector_signal"]
    logger_model["modules"]["signal_generator"]["out"] = signal_list
    logger_model["modules"]["logger"]["in"] = signal_list

    # run LiCoRICE
    licorice.go(
        logger_model,
        confirm=True,
        working_path=f"{pytest.test_dir}/module_code",
    )

    validate_model_output(capfd, NUM_TICKS)

    # read values written to sqlite database
    conn = sqlite3.connect(
        f"{pytest.test_dir}/module_code/run.lico/out/data_0000.db"
    )
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({TICK_TABLE_NAME});")
    col_names = [val[1] for val in cur.fetchall()]
    for n in TIME_COLNAMES:
        col_names.remove(n)
    cur.execute(f"SELECT {','.join(col_names)} FROM {TICK_TABLE_NAME};")
    values = cur.fetchall()
    assert len(values) == NUM_TICKS

    expected_list = get_expected_list(
        NUM_TICKS, dtype, seed=np.array([1] * vector_shape)
    )
    assert np.array_equal(expected_list, values)

    table_suffixes = [name.split("_")[-1] for name in col_names]
    assert len(suffixes) == len(table_suffixes)
    assert set(suffixes) == set(table_suffixes)


@pytest.mark.parametrize(
    "new_db_num_ticks, sql_logger_flush", [(12, 7), (10, 5)]
)
def test_create_new_db(new_db_num_ticks, sql_logger_flush, capfd):
    scalar_shape = 1
    dtype = np.float64
    dtype_str = "float64"

    # create LiCoRICE model dict
    logger_model = copy.deepcopy(logger_model_template)
    logger_model["config"]["new_db_num_ticks"] = new_db_num_ticks
    logger_model["config"]["sql_logger_flush"] = sql_logger_flush
    logger_model["signals"] = {
        "vector_signal": {
            "shape": scalar_shape,
            "dtype": dtype_str,
            "log": {"type": "vector"},
        }
    }
    signal_list = ["vector_signal"]
    logger_model["modules"]["signal_generator"]["out"] = signal_list
    logger_model["modules"]["logger"]["in"] = signal_list

    # run LiCoRICE
    licorice.go(
        logger_model,
        confirm=True,
        working_path=f"{pytest.test_dir}/module_code",
    )

    validate_model_output(capfd, NUM_TICKS)

    # read values written to sqlite databases
    values = []
    num_dbs = math.ceil(NUM_TICKS / new_db_num_ticks)
    for i in range(num_dbs):
        conn = sqlite3.connect(
            f"{pytest.test_dir}/module_code/run.lico/out/data_000{i}.db"
        )
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({TICK_TABLE_NAME});")
        col_names = [val[1] for val in cur.fetchall()]
        for n in TIME_COLNAMES:
            col_names.remove(n)
        cur.execute(f"SELECT {','.join(col_names)} FROM {TICK_TABLE_NAME};")
        vals = cur.fetchall()
        if i == num_dbs - 1:
            assert (
                len(vals) == (NUM_TICKS % new_db_num_ticks) or new_db_num_ticks
            )
        else:
            assert len(vals) == new_db_num_ticks
        values.extend([val[0] for val in vals])
    assert len(values) == NUM_TICKS

    expected_list = get_expected_list(NUM_TICKS, dtype)
    assert np.array_equal(expected_list, values)


def test_logging_from_source(capfd):
    sig_type = "float64"
    sig_name = f"{sig_type}_signal"

    # sine wave args
    fs = 1000
    f = 10
    amplitude = 10
    offset = 0

    # create LiCoRICE model dict
    logger_model = copy.deepcopy(logger_model_template)
    logger_model["config"]["num_ticks"] = NUM_TICKS
    logger_model["signals"] = {
        sig_name: {
            "shape": 10,
            "dtype": sig_type,
            "log": True,
        }
    }
    signal_list = [sig_name]
    logger_model["modules"]["signal_generator"]["in"] = {
        "name": "shared_array_test_input",
        "args": {
            "type": "signal_generator",
            "sig_name": "bnc",
            "signals": [{
                "type": "sine",
                "fs": fs,  # sampling frequency, Hz
                "f": f,  # signal frequency, Hz
                "amplitude": amplitude,
                "offset": offset,
            }]
        },
        "schema": {
            "max_packets_per_tick": 1,
            "data": {
                "dtype": sig_type,
                "size": 10,
            },
        },
        "async": False,
    }
    logger_model["modules"]["signal_generator"]["out"] = signal_list
    logger_model["modules"]["logger"]["in"] = signal_list

    # run LiCoRICE
    licorice.go(
        logger_model,
        confirm=True,
        working_path=f"{pytest.test_dir}/module_code",
        template_path=f"{pytest.test_dir}/templates",
    )

    validate_model_output(capfd, NUM_TICKS)

    # read values written to sqlite database
    conn = sqlite3.connect(
        f"{pytest.test_dir}/module_code/run.lico/out/data_0000.db"
    )
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({TICK_TABLE_NAME});")
    col_names = [val[1] for val in cur.fetchall()]
    for n in TIME_COLNAMES:
        col_names.remove(n)
    cur.execute(f"SELECT {','.join(col_names)} FROM {TICK_TABLE_NAME};")
    values = [
        value for value in cur.fetchall()
    ]
    assert len(values) == NUM_TICKS

    values = np.array(values).flatten()
    t = np.linspace(0, 1, int(fs), endpoint=False)
    expected = amplitude * np.sin(2 * np.pi * f * t, dtype=np.float64) + offset
    assert np.allclose(expected, values)


def test_signal_and_custom_tables(capfd):
    num_ticks = 10
    tick_len = 10000
    signal_table_type = "int64"
    sig_name = f"{signal_table_type}_signal"

    custom_table_types = ["float32", "int8"]
    custom_sig_names = [f"{dtype}_signal" for dtype in custom_table_types]
    custom_signals = {
        f"{dtype}_signal": {
            "shape": 1,
            "dtype": dtype,
            "log": {"enable": True, "table": "custom"},
            "max_packets_per_tick": 11,
        }
        for dtype in custom_table_types
    }

    # create LiCoRICE model dict
    logger_model = copy.deepcopy(logger_model_template)
    logger_model["config"]["num_ticks"] = num_ticks
    logger_model["config"]["tick_len"] = tick_len
    logger_model["signals"] = {
        sig_name: {
            "shape": (1,),
            "dtype": signal_table_type,
            "log": {"enable": True, "table": f"{sig_name}"},
            "max_packets_per_tick": 11,
        },
        **custom_signals
    }
    logger_model["modules"]["shared_array_in"] = {
        "language": "python",
        "in": {
            "name": "shared_array_test_input",
            "args": {
                "type": "shared_array_test",
                "sig_name": "test_sa_in",
                "func": "uniform",
                "kwargs": {
                    "low": 0.001,
                    "high": 0.002,
                },
            },
            "schema": {
                "max_packets_per_tick": 11,
                "data": {
                    "dtype": signal_table_type,
                    "size": 1,
                },
            },
            "async": True,
        },
        "out": [sig_name],
    }
    logger_model["modules"]["logger"]["in"] = [sig_name, *custom_sig_names]

    sa_sig_name = logger_model["modules"]["shared_array_in"]["in"][
        "args"
    ]["sig_name"]
    sa_sig = create_shared_array(sa_sig_name, 100, np.uint64)
    for i in range(sa_sig.size):
        sa_sig[i] = i + 1

    logger_model["modules"]["signal_generator"]["out"] = custom_sig_names

    # run LiCoRICE
    licorice.go(
        logger_model,
        confirm=True,
        working_path=f"{pytest.test_dir}/module_code",
        template_path=f"{pytest.test_dir}/templates",
    )

    sa.delete(sa_sig_name)

    validate_model_output(capfd, num_ticks)

    # validate async signal
    conn = sqlite3.connect(
        f"{pytest.test_dir}/module_code/run.lico/out/data_0000.db"
    )
    cur = conn.cursor()
    cur.execute(f"SELECT time_tick FROM {sig_name};")
    ticks = [np.int64(value[0]) for value in cur.fetchall()]

    cur.execute(f"SELECT v_i8_int64_signal_0 FROM {sig_name};")
    values = [vals[0] for vals in cur.fetchall()]

    assert len(values) > 0
    assert len(ticks) == len(values)

    for i in range(1, len(ticks)):
        assert ticks[i] - ticks[i-1] in [0, 1]

    for i in range(1, len(values)):
        assert (
            (values[i] == 1 and values[i - 1] == 100) or
            (values[i] - values[i - 1] == 1)
        )

    # validate synchronous signals
    cur.execute("SELECT time_tick FROM custom;")
    ticks = [np.int64(value[0]) for value in cur.fetchall()]
    cur.execute("SELECT r_i1_int8_signal, r_f4_float32_signal FROM custom;")
    ints_and_floats = cur.fetchall()
    ints = [vals[0] for vals in ints_and_floats]
    floats = [vals[1] for vals in ints_and_floats]

    assert len(ints) > 0
    assert len(floats) > 0
    assert len(ticks) == len(ints)
    assert len(ticks) == len(floats)

    for i in range(1, len(ticks)):
        assert ticks[i] - ticks[i - 1] == 1

    for i in range(1, len(ints)):
        assert (
            (ints[i] == 1 and ints[i - 1] == 100) or
            (ints[i] - ints[i - 1] == 1)
        )

    for i in range(1, len(floats)):
        assert (
            (ints[i] == 1. and ints[i - 1] == 100.) or
            (ints[i] - ints[i - 1] == 1.)
        )


# TODO
# potential defaults
# - system time logged in signals table
# - auto-group signals into tables from async sources
