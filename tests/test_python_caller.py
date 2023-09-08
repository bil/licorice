import pytest

import licorice
from tests.utils import validate_model_output


def test_parse_matrix_multiply(capsys):
    licorice.parse_model(
        "matrix_multiply",
        confirm=True,
        working_path=f"{pytest.examples_dir}/matrix_multiply",
    )

    captured_out, captured_err = validate_model_output(
        capsys, None, validate_stdout=False
    )
    assert "Parsing" in captured_out


def test_compile_matrix_multiply(capsys):
    licorice.compile_model(
        "matrix_multiply",
        confirm=True,
        working_path=f"{pytest.examples_dir}/matrix_multiply",
    )

    captured_out, captured_err = validate_model_output(
        capsys, None, validate_stdout=False
    )
    assert "gcc" in captured_out


def test_run_matrix_multiply(capsys):
    licorice.run_model(
        "matrix_multiply",
        confirm=True,
        working_path=f"{pytest.examples_dir}/matrix_multiply",
    )

    validate_model_output(capsys, 30)
