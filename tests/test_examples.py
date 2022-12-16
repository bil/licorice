import os
import subprocess

import pytest


def is_joystick_connected():
    import pygame

    pygame.joystick.init()
    return pygame.joystick.get_count() >= 1


@pytest.mark.xfail(raises=NotImplementedError)
def test_jitter():
    raise NotImplementedError


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
