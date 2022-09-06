import pytest
import subprocess


def test_matrix_multiply(capfd):
    subprocess.call("./examples/matrix_multiply/run.sh", shell=True)
    captured = capfd.readouterr()
    # TODO snapshottest
    assert "LiCoRICE ran for 10 ticks." in captured.out
    assert captured.err == ""


def is_joystick_connected():
    import pygame
    pygame.joystick.init()
    return pygame.joystick.get_count() >= 1

@pytest.mark.skipif(
    not is_joystick_connected(),
    reason="No joystick connected."
)
def test_joystick(capfd):
    subprocess.call("./examples/joystick/run.sh", shell=True)
    captured = capfd.readouterr()
    # TODO snapshottest
    assert "LiCoRICE ran for 21 ticks." in captured.out
    assert captured.err == ""
