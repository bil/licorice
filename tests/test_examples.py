import os
import subprocess

import pytest
from udp import udp_server_recv


def is_joystick_connected():
    import pygame

    pygame.joystick.init()
    return pygame.joystick.get_count() >= 1


def test_jitter(capfd):
    num_ticks = 1000
    subprocess.call(
        """./examples/jitter/run.sh """
        f"""--config '{{"config":{{"num_ticks":{num_ticks}}}}}'""",
        shell=True,
    )
    captured = capfd.readouterr()
    # TODO snapshottest/syrupy
    assert f"LiCoRICE ran for {num_ticks} ticks." in captured.out
    assert captured.err == ""

    with pytest.raises(Exception) as e_info:
        mean, std_dev, min_val, max_val = udp_server_recv(3333, timeout=1.)
        print(mean, std_dev, min_val, max_val)
        assert False

    print(e_info)


@pytest.mark.xfail(raises=NotImplementedError)
def test_parallel_toggle():
    raise NotImplementedError


def test_matrix_multiply(capfd):
    subprocess.call("./examples/matrix_multiply/run.sh", shell=True)
    captured = capfd.readouterr()
    # TODO snapshottest/syrupy
    assert "LiCoRICE ran for 10 ticks." in captured.out
    assert captured.err == ""


@pytest.mark.xfail(raises=NotImplementedError)
def test_logger():
    raise NotImplementedError


@pytest.mark.skipif(
    not is_joystick_connected(), reason="No joystick connected."
)
def test_joystick(capfd):
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    subprocess.call("./examples/joystick/run.sh", shell=True)
    captured = capfd.readouterr()
    # TODO snapshottest/syrupy
    assert "LiCoRICE ran for 21 ticks." in captured.out
    assert captured.err == ""


@pytest.mark.xfail(raises=NotImplementedError)
def test_pygame():
    raise NotImplementedError


@pytest.mark.xfail(raises=NotImplementedError)
def test_cursor_track():
    raise NotImplementedError


@pytest.mark.xfail(raises=NotImplementedError)
def test_pinball():
    raise NotImplementedError
