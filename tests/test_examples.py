import os
import sqlite3
import subprocess
from collections import OrderedDict

import msgpack
import parallel
import pygame
import pytest
from udp import udp_server_recv

from tests.utils import TIME_COLNAMES, validate_model_output


def num_parports():
    num_ports = 0
    for i in range(4):
        try:
            parallel.Parallel(port=i)
            num_ports += 1
        except FileNotFoundError:
            pass

    return num_ports


def has_joystick():
    pygame.joystick.init()
    return pygame.joystick.get_count() >= 1


# TODO create better test that senses if ESP32 is connected
@pytest.mark.skipif(
    num_parports() < 1, reason="No parallel ports connected."
)
def test_jitter(capfd):
    num_ticks = 1000
    subprocess.call(
        f"""{pytest.examples_dir}/jitter/run.sh """
        f"""--config '{{"config":{{"num_ticks":{num_ticks}}}}}'""",
        shell=True,
    )

    validate_model_output(capfd, num_ticks)

    try:
        mean, std_dev, min_val, max_val = udp_server_recv(3333, timeout=1.)
        results_str = f"{mean},{std_dev},{min_val},{max_val}\n"
    except Exception as e:
        print(e)
        results_str = None

    if results_str:
        write_header = False
        if not os.path.exists(f"{pytest.test_dir}/jitter_results.csv"):
            write_header = True

        with open(f"{pytest.test_dir}/jitter_results.csv", "w") as f:
            if write_header:
                f.write("mean,std_dev,min_val,max_val\n")
            f.write(results_str)


@pytest.mark.skipif(
    num_parports() < 2, reason="Insufficient parallel ports connected."
)
def test_parallel_toggle(capfd):
    num_ticks = 1000
    subprocess.call(
        f"""{pytest.examples_dir}/parallel_toggle/run.sh """
        f"""--config '{{"config":{{"num_ticks":{num_ticks}}}}}'""",
        shell=True,
    )

    validate_model_output(capfd, num_ticks)


def test_matrix_multiply(capfd):
    num_ticks = 30
    subprocess.call(
        f"{pytest.examples_dir}/matrix_multiply/run.sh "
        f"""--config '{{"config":{{"num_ticks":{num_ticks}}}}}'""",
        shell=True
    )

    validate_model_output(capfd, num_ticks)


def test_logger(capfd, snapshot):
    num_ticks = 32
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    subprocess.call(
        f"{pytest.examples_dir}/logger/run.sh "
        f"""--config '{{"config":{{"num_ticks":{num_ticks}}}}}'""",
        shell=True
    )

    # # TODO address UserWarning for no parser. Move validation into drivers
    validate_model_output(capfd, num_ticks, validate_stderr=False)

    conn = sqlite3.connect(
        f"{pytest.examples_dir}/logger/logger_demo.lico/out/data_0000.db"
    )
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(tick);")
    col_names = [val[1] for val in cur.fetchall()]
    # don't snapshot nanosecond timers
    for n in TIME_COLNAMES[1:]:
        col_names.remove(n)

    cur.execute(f"SELECT {' ,'.join(col_names)} FROM tick;")

    col_names = [col[0] for col in cur.description]
    col_vals = [[] for _ in col_names]
    for row in cur.fetchall():
        for i in range(len(col_names)):
            val = row[i]
            if col_names[i][0] == "m":
                val = msgpack.unpackb(val)
            col_vals[i].append(val)
    table_dict = OrderedDict(sorted(dict(zip(col_names, col_vals)).items()))
    assert table_dict == snapshot


@pytest.mark.skipif(
    not has_joystick(), reason="No joystick connected."
)
def test_joystick(capfd):
    num_ticks = 21
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    subprocess.call(f"{pytest.examples_dir}/joystick/run.sh", shell=True)

    validate_model_output(capfd, num_ticks)


def test_pygame(capfd):
    num_ticks = 100
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    subprocess.call(
        f"{pytest.examples_dir}/pygame/run.sh "
        f"""--config '{{"config":{{"num_ticks":{num_ticks}}}}}'""",
        shell=True
    )

    validate_model_output(capfd, num_ticks)


@pytest.mark.skipif(
    not has_joystick(), reason="No joystick connected."
)
def test_cursor_track(capfd):
    num_ticks = 100
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    subprocess.call(
        f"{pytest.examples_dir}/cursor_track/run.sh "
        f"""--config '{{"config":{{"num_ticks":{num_ticks}}}}}'""",
        shell=True
    )

    # TODO address UserWarning for no parser. Move validation into drivers
    validate_model_output(capfd, num_ticks, validate_stderr=False)


@pytest.mark.skipif(
    not has_joystick(), reason="No joystick connected."
)
def test_pinball(capfd):
    num_ticks = 100
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    subprocess.call(
        f"{pytest.examples_dir}/pinball/run.sh "
        f"""--config '{{"config":{{"num_ticks":{num_ticks}}}}}'""",
        shell=True
    )

    # TODO address UserWarning for no parser. Move validation into drivers
    validate_model_output(capfd, num_ticks, validate_stderr=False)


def test_udp(capfd):
    proc = subprocess.Popen([f"{pytest.examples_dir}/udp/send_udp.sh"])

    subprocess.call(
        f"""{pytest.examples_dir}/udp/run.sh """
        f"""--config '{{"config":{{"num_ticks":{600}}}}}'""",
        shell=True,
    )

    proc.terminate()

    captured = capfd.readouterr()
    print(captured.out)
    print(captured.err)
    msgs = ["STAN", "FORD", "TREE", "MESS", "AGES"]
    for msg in msgs:
        assert msg in captured.out


@pytest.mark.xfail(raises=NotImplementedError)
def test_sine(capfd):
    raise NotImplementedError


@pytest.mark.xfail(raises=NotImplementedError)
def test_audio_capture(capfd):
    raise NotImplementedError


@pytest.mark.xfail(raises=NotImplementedError)
def test_polaris(capfd):
    raise NotImplementedError
