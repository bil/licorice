import warnings

import pytest

import licorice

NUM_TICKS = 1000

sink_parser_model = {
    "config": {
        "tick_len": 10000,
        "num_ticks": NUM_TICKS,
    },
    "signals": {
        "signal_1": {
            "shape": 1,
            "dtype": "uint8",
        },
        "signal_2": {
            "shape": 1,
            "dtype": "uint8",
        },
    },
    "modules": {
        "parport_generator": {
            "language": "python",
            "constructor": True,
            "parser": True,
            "out": ["signal_1", "signal_2"],
        },
        "parport_writer": {
            "language": "python",
            "parser": True,
            "in": ["signal_1", "signal_2"],
            "out": {
                "name": "parport_out",
                "schema": {
                    "data": {
                        "size": 1,
                        "dtype": "uint8",
                    }
                },
                "args": {
                    "type": "parport",
                    "addr": "1",
                },
            },
        },
    },
}


def has_parallel_port():
    import parallel

    try:
        parallel.Parallel()
    except FileNotFoundError:
        return False
    except OSError:
        warnings.warn("Default parallel port is busy.")
    return True


@pytest.mark.skipif(
    not has_parallel_port(), reason="No parallel port detected."
)
def test_sink_parser(capfd):
    # run LiCoRICE with sink parser
    licorice.go(
        sink_parser_model,
        confirm=True,
        working_path=f"{pytest.test_dir}/module_code",
    )

    # check LiCoRICE stdout and stderr output
    captured = capfd.readouterr()
    assert f"LiCoRICE ran for {NUM_TICKS} ticks." in captured.out
    assert captured.err == ""
