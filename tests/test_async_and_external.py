import copy
import re
import subprocess

import numpy as np
import pytest
import SharedArray as sa

import licorice
from licorice.templates.module_utils import create_shared_array
from tests.utils import validate_model_output

NUM_TICKS = 100

async_reader_model = {
    "config": {
        "tick_len": 10000,
        "num_ticks": NUM_TICKS,
    },
    "signals": {
        "uint64_signal": {
            "shape": 1,
            "dtype": "uint64",
            "max_packets_per_tick": 3,
        },
    },
    "modules": {
        "shared_array_in": {
            "language": "python",
            "in": {
                "name": "shared_array_input",
                "args": {
                    "type": "shared_array",
                    "sig_name": "test_sa_in",
                    "func": "uniform",
                    "kwargs": {
                        "low": 0.005,
                        "high": 0.01,
                    },
                },
                "schema": {
                    "max_packets_per_tick": 3,
                    "data": {
                        "dtype": "uint64",
                        "size": 1,
                    },
                },
                "async": True,
            },
            "out": ["uint64_signal"],
        },
        "shared_array_print": {
            "language": "python",
            "parser": True,
            "in": ["uint64_signal"],
        },
    },
}


def test_async_reader(capfd):
    sa_sig_name = async_reader_model["modules"]["shared_array_in"]["in"][
        "args"
    ]["sig_name"]
    sa_sig = create_shared_array(f"shm://{sa_sig_name}", 100, np.uint64)
    for i in range(sa_sig.size):
        sa_sig[i] = i + 1

    # run LiCoRICE with sink parser
    try:
        licorice.go(
            async_reader_model,
            confirm=True,
            working_path=f"{pytest.test_dir}/module_code",
            template_path=f"{pytest.test_dir}/templates",
        )
    except subprocess.CalledProcessError:
        pass

    sa.delete(sa_sig_name)

    captured_out, captured_err = validate_model_output(capfd, NUM_TICKS)

    # check output is sequential
    vals = [
        int(val)
        for val in re.findall(
            r"shared_array_print_output: (\d+)", captured_out
        )
    ]
    for i in range(1, len(vals)):
        assert vals[i] - vals[i - 1] == 1


async_writer_model = {
    "config": {
        "tick_len": 10000,
        "num_ticks": NUM_TICKS,
    },
    "signals": {
        "uint64_signal": {
            "shape": 1,
            "dtype": "uint64",
        }
    },
    "modules": {
        "signal_generator": {
            "language": "python",
            "constructor": True,
            "out": ["uint64_signal"],
        },
        "shared_array_out": {
            "language": "python",
            "in": ["uint64_signal"],
            "out": {
                "name": "shared_array_output",
                "args": {
                    "type": "shared_array",
                    "sig_name": "test_sa_out",
                    "func": "normal",
                    "kwargs": {
                        "loc": 0.001,
                        "scale": 0.00025,
                    },
                },
                "schema": {
                    "data": {
                        "dtype": "uint64",
                        "size": 1,
                    }
                },
                "async": True,
            },
        },
    },
}


def test_async_writer(capfd):
    sa_sig_name = async_writer_model["modules"]["shared_array_out"]["out"][
        "args"
    ]["sig_name"]
    sa_sig = create_shared_array(sa_sig_name, 100, np.uint64)

    # run LiCoRICE with sink parser
    licorice.go(
        async_writer_model,
        confirm=True,
        working_path=f"{pytest.test_dir}/module_code",
        template_path=f"{pytest.test_dir}/templates",
    )

    sa_sig = sa_sig.copy()
    sa.delete(sa_sig_name)

    validate_model_output(capfd, NUM_TICKS)

    # check output is sequential starting at 1
    assert sa_sig[0] == 1
    for i in range(1, len(sa_sig)):
        assert sa_sig[i] - sa_sig[i - 1] == 1


@pytest.mark.xfail(raises=NotImplementedError)
def test_async_module():
    raise NotImplementedError


async_combo_model = copy.deepcopy(async_reader_model)
async_combo_model["modules"].update(
    {
        "shared_array_out": {
            "language": "python",
            "in": ["uint64_signal"],
            "out": {
                "name": "shared_array_output",
                "args": {
                    "type": "shared_array",
                    "sig_name": "test_sa_out",
                    "func": "normal",
                    "kwargs": {
                        "loc": 0.001,
                        "scale": 0.00025,
                    },
                },
                "schema": {
                    "data": {
                        "dtype": "uint64",
                        "size": 1,
                    }
                },
                "async": True,
            },
        }
    }
)


def test_async_combo(capfd):
    # TODO have this use an async module as well

    sa_sig_in_name = "test_sa_in"
    sa_sig_in = create_shared_array(sa_sig_in_name, 100, np.uint64)
    for i in range(sa_sig_in.size):
        sa_sig_in[i] = i + 1

    sa_sig_out_name = "test_sa_out"
    sa_sig_out = create_shared_array(sa_sig_out_name, 100, np.uint64)

    # run LiCoRICE with sink parser
    print(async_combo_model)
    licorice.go(
        async_combo_model,
        confirm=True,
        working_path=f"{pytest.test_dir}/module_code",
        template_path=f"{pytest.test_dir}/templates",
    )

    sa_sig_out = sa_sig_out.copy()
    sa.delete(sa_sig_in_name)
    sa.delete(sa_sig_out_name)

    validate_model_output(capfd, NUM_TICKS)

    # check output is sequential
    print(sa_sig_out)
    for i in range(1, len(sa_sig_out)):
        assert (sa_sig_out[i - 1] == 100) or (
            sa_sig_out[i] - sa_sig_out[i - 1] == 1
        )


skip_ticks_latency_model = {
    "config": {
        "tick_len": 10000,
        "num_ticks": NUM_TICKS,
        "module_init_ticks": 1,
    },
    "signals": {
        "count": {
            "shape": 1,
            "dtype": "int32",
        },
    },
    "modules": {
        "count_writer": {
            "language": "python",
            "constructor": True,
            "out": ["count"]
        },
        "printer": {
            "language": "python",
            "parser": True,
            "in": ["count"],
            "out": {
                "name": "console_out",
                "async": True,
                "args": {
                    "type": "console",
                },
            },
        },
    },
}


@pytest.mark.parametrize(
    "skip_ticks, latency",
    [(1, 0), (0, 1)],
)
def test_skip_ticks_and_latency(skip_ticks, latency, capfd):
    skip_ticks_latency_model["modules"]["printer"]["out"]["args"][
        "skip_ticks"
    ] = skip_ticks
    skip_ticks_latency_model["signals"]["count"]["latency"] = latency

    # run external driver model with LiCoRICE
    licorice.go(
        skip_ticks_latency_model,
        confirm=True,
        working_path=f"{pytest.test_dir}/module_code",
        template_path=f"{pytest.test_dir}/templates",
    )

    captured_out, captured_err = validate_model_output(capfd, NUM_TICKS)

    # check output is sequential by 2
    vals = [
        int(val)
        for val in re.findall(
            r"console_out: (-?\d+)", captured_out
        )
    ]
    assert vals[0] == -1 * latency
    for i in range(1, len(vals) - 1):
        assert vals[i] - vals[i - 1] == skip_ticks + 1
