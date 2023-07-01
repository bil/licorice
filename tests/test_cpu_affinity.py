import copy
import platform
import subprocess
import time
from multiprocessing import Process

import numpy as np
import psutil
import pytest
import SharedArray as sa

import licorice
from licorice.templates.module_utils import create_shared_array

small_model = {
    "config": {
        "tick_len": 10000,
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
                "name": "shared_array_test_input",
                "args": {
                    "type": "shared_array_test",
                    "sig_name": "test_sa_in",
                    "func": "normal",
                    "kwargs": {
                        "loc": 0.001,
                        "scale": 0.00025,
                    },
                },
                "schema": {
                    "max_packets_per_tick": 3,
                    "data": {
                        "dtype": "uint64",
                        "size": 1,
                    },
                },
                "async": False,
            },
            "out": ["uint64_signal"],
        },
        "shared_array_out": {
            "language": "python",
            "in": ["uint64_signal"],
            "out": {
                "name": "shared_array_test_output",
                "args": {
                    "type": "shared_array_test",
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
                "async": False,
            },
        }
    },
}

sync_model = copy.deepcopy(small_model)
sync_model["signals"]["out_1_1"] = {
    "shape": 1,
    "dtype": "uint64",
    "max_packets_per_tick": 3,
}
sync_model["signals"]["out_2_1"] = {
    "shape": 1,
    "dtype": "uint64",
    "max_packets_per_tick": 3,
}
sync_model["modules"]["shared_array_print_1_1"] = {
    "language": "python",
    "parser": True,
    "in": ["uint64_signal"],
    "out": ["out_1_1"],
}
sync_model["modules"]["shared_array_print_2_1"] = {
    "language": "python",
    "parser": True,
    "in": ["out_1_1"],
    "out": ["out_2_1"],
}
sync_model["modules"]["shared_array_out"]["in"] = ["out_2_1"]

async_model = copy.deepcopy(sync_model)
async_model["modules"]["shared_array_in"]["in"]["async"] = True
async_model["modules"]["shared_array_out"]["out"]["async"] = True

async_large_model = copy.deepcopy(async_model)
async_large_model["signals"]["out_1_2"] = {
    "shape": 1,
    "dtype": "uint64",
    "max_packets_per_tick": 3,
}
async_large_model["signals"]["out_2_2"] = {
    "shape": 1,
    "dtype": "uint64",
    "max_packets_per_tick": 3,
}
async_large_model["modules"]["shared_array_print_1_2"] = {
    "language": "python",
    "parser": True,
    "in": ["uint64_signal"],
    "out": ["out_1_2"],
}
async_large_model["modules"]["shared_array_print_2_2"] = {
    "language": "python",
    "parser": True,
    "in": ["out_1_2"],
    "out": ["out_2_2"],
}

# assumes we're running on a test computer with at least 4 available cores
# 8 cores required for full test
TEST_ARGS = [
    (  # case 8
        async_model,
        1,
        1,
        {
            "timer": "1",
            "shared_array_in_async_reader": "1",
            "shared_array_in": "1",
            "shared_array_print_1_1": "1",
            "shared_array_print_2_1": "1",
            "shared_array_out": "1",
            "shared_array_out_async_writer": "1",
        }
    ),
    (  # case 7
        async_model,
        2,
        1,
        {
            "timer": "2",
            "shared_array_in_async_reader": "2",
            "shared_array_in": "2",
            "shared_array_print_1_1": "2",
            "shared_array_print_2_1": "2",
            "shared_array_out": "2",
            "shared_array_out_async_writer": "2",
        }
    ),
    (  # case 6
        async_large_model,
        3,
        2,
        {
            "timer": "2",
            "shared_array_in_async_reader": "4",
            "shared_array_in": "4",
            "shared_array_print_1_1": "4",
            "shared_array_print_1_2": "4",
            "shared_array_print_2_1": "4",
            "shared_array_print_2_2": "4",
            "shared_array_out": "4",
            "shared_array_out_async_writer": "4",
        }
    ),
    (  # case 5
        async_model,
        3,
        2,
        {
            "timer": "2",
            "shared_array_in_async_reader": "1",
            "shared_array_in": "4",
            "shared_array_print_1_1": "4",
            "shared_array_print_2_1": "4",
            "shared_array_out": "4",
            "shared_array_out_async_writer": "1",
        }
    ),
    (   # case 4
        async_model,
        4,
        3,
        {
            "timer": "2",
            "shared_array_in_async_reader": "4",
            "shared_array_in": "8",
            "shared_array_print_1_1": "8",
            "shared_array_print_2_1": "8",
            "shared_array_out": "8",
            "shared_array_out_async_writer": "4",
        }
    ),
    (   # case 3
        async_model,
        6,
        5,
        {
            "timer": "2",
            "shared_array_in_async_reader": "4",
            "shared_array_in": "8",
            "shared_array_print_1_1": "20",
            "shared_array_print_2_1": "20",
            "shared_array_out": "10",
            "shared_array_out_async_writer": "4",
        }
    ),
    (   # case 2
        async_model,
        7,
        6,
        {
            "timer": "2",
            "shared_array_in_async_reader": "4",
            "shared_array_in": "8",
            "shared_array_print_1_1": "20",
            "shared_array_print_2_1": "40",
            "shared_array_out": "10",
            "shared_array_out_async_writer": "4",
        }
    ),
    (   # case 1, 4 cores
        small_model,
        4,
        3,
        {
            "timer": "2",
            "shared_array_in": "4",
            "shared_array_out": "8",
        }
    ),
    (   # case 1, 8 cores
        async_model,
        8,
        7,
        {
            "timer": "2",
            "shared_array_in_async_reader": "4",
            "shared_array_in": "8",
            "shared_array_print_1_1": "20",
            "shared_array_print_2_1": "40",
            "shared_array_out": "10",
            "shared_array_out_async_writer": "80",
        }
    ),
]


def run_cmd(cmd_str):
    process = subprocess.Popen(cmd_str, shell=True, stdout=subprocess.PIPE)
    return process.communicate()


def parse_and_compile_model(*args, **kwargs):
    # parse and compile LiCoRICE model
    try:
        p = Process(
            target=licorice.parse_model,
            args=args,
            kwargs=kwargs,
        )
        p.start()
        p.join()
        p = Process(
            target=licorice.compile_model,
            args=args,
            kwargs=kwargs,
        )
        p.start()
        p.join()
    except subprocess.CalledProcessError:
        pass


def get_proc_pid(name, thread=False):
    if thread:
        line_idx = 1
        pid_idx = 2
    else:
        pid_idx = 1
    while (len(cmd_output := (run_cmd(
        f"ps -T aux | grep {name} | grep -v grep"
    )[0].split(b"\n"))) == 0):
        time.sleep(0.1)
    if thread:
        return int(cmd_output[line_idx].split()[pid_idx])
    else:
        for line in cmd_output:
            if len(line) == 0:
                continue
            if line.split()[11].decode()[2:] == name:
                return int(line.split()[pid_idx])


@pytest.mark.skipif(
    platform.system() ==
    "Darwin", reason="CPU affinity not implemented on Darwin."
)
@pytest.mark.parametrize(
    "model, num_cores, lico_cores, affinity_map",
    [tup for tup in TEST_ARGS],
)
def test_core_assignment(
    model, num_cores, lico_cores, affinity_map, capfd, monkeypatch
):
    if psutil.cpu_count() < num_cores:
        pytest.skip()
    monkeypatch.setattr(psutil, "cpu_count", lambda: num_cores)

    sa_sig = create_shared_array("shm://test_sa_in", 100, np.uint64)
    for i in range(sa_sig.size):
        sa_sig[i] = i + 1
    sa_sig_out = create_shared_array("shm://test_sa_out", 100, np.uint64)

    parse_and_compile_model(
        model,
        confirm=True,
        working_path=f"{pytest.test_dir}/module_code/cpu_affinity",
        template_path=f"{pytest.test_dir}/templates"
    )

    captured = capfd.readouterr()
    captured_out = captured.out
    captured_err = captured.err
    print(captured_out)
    print(captured_err)
    assert captured_err == ""

    # run LiCoRICE
    try:
        p = Process(
            target=licorice.run_model,
            args=(model,),
            kwargs={
                "confirm": True,
                "working_path": f"{pytest.test_dir}/module_code/cpu_affinity",
                "template_path": f"{pytest.test_dir}/templates",
            }
        )
        p.start()
        while "Timer thread started." not in (out := capfd.readouterr().out):
            time.sleep(0.1)
            captured_out += out
    except Exception as e:
        print(e)
        p.join()
        captured = capfd.readouterr()
        captured_out += captured.out
        captured_err += captured.err
        print(captured_out)
        print(captured_err)
        assert False

    proc_names = ["timer"] + list(model["modules"].keys())
    if model != small_model:
        proc_names += [
            "shared_array_in_async_reader", "shared_array_out_async_writer",
        ]
    proc_affinities = {}
    for name in proc_names:
        pid = get_proc_pid(name, thread=(name == "timer"))
        affinity = run_cmd(f"taskset -p {pid}")[0].split(
            b"affinity mask:", 1
        )[1].strip()
        proc_affinities[name] = affinity.decode()

    timer_pid = get_proc_pid("timer")
    run_cmd(f"kill -s INT {timer_pid}")

    p.join()

    sa_sig_out = sa_sig_out.copy()
    sa.delete("shm://test_sa_in")
    sa.delete("shm://test_sa_out")

    # check LiCoRICE stdout and stderr output
    captured = capfd.readouterr()
    captured_out += captured.out
    captured_err += captured.err
    print(captured_out)
    print(captured_err)

    assert f"LiCoRICE will run on {lico_cores} core(s)." in captured_out
    assert captured_err == ""
    assert proc_affinities == affinity_map
