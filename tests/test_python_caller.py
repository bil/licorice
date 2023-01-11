import pytest

import licorice


def test_parse_matrix_multiply(capsys):
    licorice.parse_model(
        "matrix_multiply",
        confirm=True,
        working_path=f"{pytest.examples_dir}/matrix_multiply",
    )
    captured = capsys.readouterr()
    # TODO snapshottest
    assert "Parsing" in captured.out
    assert captured.err == ""


def test_compile_matrix_multiply(capsys):
    licorice.compile_model(
        "matrix_multiply",
        confirm=True,
        working_path=f"{pytest.examples_dir}/matrix_multiply",
    )
    captured = capsys.readouterr()
    # TODO snapshottest
    assert "gcc" in captured.out
    assert captured.err == ""


def test_run_matrix_multiply(capsys):
    licorice.run_model(
        "matrix_multiply",
        confirm=True,
        working_path=f"{pytest.examples_dir}/matrix_multiply",
    )
    captured = capsys.readouterr()
    # TODO snapshottest
    assert "LiCoRICE ran for 30 ticks." in captured.out
    assert captured.err == ""
