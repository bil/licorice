TIME_COLNAMES = [
    "time_tick", "time_monotonic_raw", "time_monotonic", "time_realtime"
]


def validate_model_output(
    cf, num_ticks, validate_stdout=True, validate_stderr=True
):
    """Check LiCoRICE stdout and stderr output

    Args:
        cf (CaptureFixture[str]): pytest captured output object
        num_ticks (int): Expected number of ticks for LiCoRICE model to run.
        validate_stdout (bool): Whether or not stdout should be validated.
            True by default.
        validate_stderr (bool): Whether or not stderr should be validated.
            True by default.

    """

    # TODO add snapshottest/syrupy

    captured_out, captured_err = cf.readouterr()
    print(captured_out, flush=True)
    print(captured_err, flush=True)
    if validate_stdout:
        assert "Seg Fault" not in captured_out
        assert f"LiCoRICE ran for {num_ticks} ticks." in captured_out
    if validate_stderr:
        assert captured_err == ""

    return captured_out, captured_err
