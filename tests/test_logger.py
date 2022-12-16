import copy
import math
import sqlite3

import msgpack
import numpy as np
import pytest

import licorice

NUM_TICKS = 100

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
SIMPLE_TICKS = [10, 1000]


def get_expected_list(num_ticks, dtype, seed=None):
    if seed is None:
        seed = dtype(1)

    expected_list = []
    for i in range(num_ticks):
        expected_list.append(seed + (i % 100))
    return np.array(expected_list)


# test logging one signal of each type:
@pytest.mark.parametrize(
    "sig_type, num_ticks",
    [(dtype, ticks) for dtype in TEST_DTYPES for ticks in SIMPLE_TICKS],
)
def test_single_signal(sig_type, num_ticks, capfd):
    sig_name = f"{sig_type}_signal"

    # create LiCoRICE model dict
    logger_model = copy.deepcopy(logger_model_template)
    logger_model["config"]["num_ticks"] = num_ticks
    logger_model["signals"] = {
        sig_name: {
            "shape": 1,
            "dtype": sig_type,
            "log": True,
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

    # check LiCoRICE stdout and stderr output
    captured = capfd.readouterr()
    assert f"LiCoRICE ran for {num_ticks} ticks." in captured.out
    assert captured.err == ""

    # read values written to sqlite database
    conn = sqlite3.connect(
        f"{pytest.test_dir}/module_code/run.lico/out/data_0000.db"
    )
    cur = conn.cursor()
    cur.execute("SELECT * FROM signals;")
    sig_dtype = np.dtype(sig_type).type
    values = [sig_dtype(value[0]) for value in cur.fetchall()]
    assert len(values) == num_ticks

    expected_list = get_expected_list(num_ticks, sig_dtype)
    assert np.array_equal(expected_list, values)


def test_vector(capfd):
    vector_shape = 10
    dtype = np.int32
    dtype_str = "int32"

    # create LiCoRICE model dict
    logger_model = copy.deepcopy(logger_model_template)
    logger_model["signals"] = {
        "vector_signal": {
            "shape": vector_shape,
            "dtype": dtype_str,
            "log": True,
            "log_storage": {"type": "vector"},
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

    # check LiCoRICE stdout and stderr output
    captured = capfd.readouterr()
    assert f"LiCoRICE ran for {NUM_TICKS} ticks." in captured.out
    assert captured.err == ""

    # read values written to sqlite database
    conn = sqlite3.connect(
        f"{pytest.test_dir}/module_code/run.lico/out/data_0000.db"
    )
    cur = conn.cursor()
    cur.execute("SELECT * FROM signals;")
    values = cur.fetchall()
    assert len(values) == NUM_TICKS

    expected_list = get_expected_list(
        NUM_TICKS, dtype, seed=np.array([1] * vector_shape)
    )
    assert np.array_equal(expected_list, values)


def test_msgpack(capfd):
    matrix_shape = (4, 4)
    dtype = np.float32
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

    # check LiCoRICE stdout and stderr output
    captured = capfd.readouterr()
    assert f"LiCoRICE ran for {NUM_TICKS} ticks." in captured.out
    assert captured.err == ""

    # read values written to sqlite database
    conn = sqlite3.connect(
        f"{pytest.test_dir}/module_code/run.lico/out/data_0000.db"
    )
    cur = conn.cursor()
    cur.execute("SELECT * FROM signals;")
    values = [
        np.array(msgpack.unpackb(value[0])).reshape(matrix_shape)
        for value in cur.fetchall()
    ]
    assert len(values) == NUM_TICKS

    expected_list = get_expected_list(
        NUM_TICKS, dtype, seed=np.array(np.ones(matrix_shape))
    )
    assert np.array_equal(expected_list, values)


def test_multi_signal(capfd):
    signals_dict = {}
    signal_list = []
    dict_vals = [
        ("scalar", 1, None),
        ("vector", 5, {"type": "vector"}),
        ("matrix", (2, 2), None),
    ]
    for dtype in TEST_DTYPES:
        for name, shape, log_storage in dict_vals:
            sig_name = f"{name}_{dtype}_signal"
            signals_dict[sig_name] = {
                "shape": shape,
                "dtype": dtype,
                "log": True,
            }
            if log_storage:
                signals_dict[sig_name]["log_storage"] = log_storage
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

    # check LiCoRICE stdout and stderr output
    captured = capfd.readouterr()
    assert f"LiCoRICE ran for {NUM_TICKS} ticks." in captured.out
    assert captured.err == ""

    # read values written to sqlite database
    conn = sqlite3.connect(
        f"{pytest.test_dir}/module_code/run.lico/out/data_0000.db"
    )
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(signals);")
    col_names = [val[1] for val in cur.fetchall()]
    cur.execute(f"SELECT {','.join(col_names)} FROM signals;")
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
            "log": True,
            "log_storage": {"type": "vector", "suffixes": suffixes},
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

    # check LiCoRICE stdout and stderr output
    captured = capfd.readouterr()
    assert f"LiCoRICE ran for {NUM_TICKS} ticks." in captured.out
    assert captured.err == ""

    # read values written to sqlite database
    conn = sqlite3.connect(
        f"{pytest.test_dir}/module_code/run.lico/out/data_0000.db"
    )
    cur = conn.cursor()
    cur.execute("SELECT * FROM signals;")
    values = cur.fetchall()
    assert len(values) == NUM_TICKS

    expected_list = get_expected_list(
        NUM_TICKS, dtype, seed=np.array([1] * vector_shape)
    )
    assert np.array_equal(expected_list, values)

    cur.execute("PRAGMA table_info(signals);")
    table_suffixes = [val[1].split("_")[-1] for val in cur.fetchall()]
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
            "log": True,
            "log_storage": {"type": "vector"},
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

    # check LiCoRICE stdout and stderr output
    captured = capfd.readouterr()
    assert f"LiCoRICE ran for {NUM_TICKS} ticks." in captured.out
    assert captured.err == ""

    # read values written to sqlite databases
    values = []
    num_dbs = math.ceil(NUM_TICKS / new_db_num_ticks)
    for i in range(num_dbs):
        conn = sqlite3.connect(
            f"{pytest.test_dir}/module_code/run.lico/out/data_000{i}.db"
        )
        cur = conn.cursor()
        cur.execute("SELECT * FROM signals;")
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
