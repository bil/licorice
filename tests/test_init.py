import numpy as np
import pytest
import SharedArray as sa

import licorice
from licorice.templates.module_utils import create_shared_array
from tests.utils import validate_model_output

NUM_TICKS = 10
SRC_INIT_TICKS = 10
MOD_INIT_TICKS = 10
TOTAL_TICKS = NUM_TICKS + SRC_INIT_TICKS + MOD_INIT_TICKS

init_ticks_model = {
    "config": {
        "tick_len": 10000,
        "num_ticks": NUM_TICKS,
        "source_init_ticks": SRC_INIT_TICKS,
        "module_init_ticks": MOD_INIT_TICKS
    },
    "signals": {
        "uint64_signal_in": {
            "shape": 1,
            "dtype": "uint64",
        },
        "uint64_signal_out": {
            "shape": 1,
            "dtype": "uint64",
        },

    },
    "modules": {
        "init_source": {
            "language": "python",
            "parser": True,
            "constructor": True,
            "in": {
                "name": "shared_array_input",
                "args": {
                    "type": "shared_array",
                    "sig_name": "test_sa_in",
                },
                "schema": {
                    "max_packets_per_tick": 3,
                    "data": {
                        "dtype": "uint64",
                        "size": 1,
                    },
                },
            },
            "out": ["uint64_signal_in"],
        },
        "init_module": {
            "language": "python",
            "parser": True,
            "constructor": True,
            "in": ["uint64_signal_in"],
            "out": ["uint64_signal_out"],
        },
        "init_sink": {
            "language": "python",
            # "parser": True,
            "in": ["uint64_signal_out"],
            "out": {
                "name": "shared_array_output",
                "args": {
                    "type": "shared_array",
                    "sig_name": "test_sa_snk",
                },
                "schema": {
                    "max_packets_per_tick": 3,
                    "data": {
                        "dtype": "uint64",
                        "size": 1,
                    },
                },
            },
        }
    },
}


def test_init_ticks(capfd):
    sa_sig_name_in = init_ticks_model["modules"]["init_source"]["in"]["args"][
        "sig_name"
    ]
    sa_sig_in = create_shared_array(sa_sig_name_in, 30, np.uint64)
    for i in range(sa_sig_in.size):
        sa_sig_in[i] = i + 1

    sa_sig_name_src = "test_sa_src"
    sa_sig_src = create_shared_array(sa_sig_name_src, 30, np.uint64)
    sa_sig_src[:] = 0

    sa_sig_name_mod = "test_sa_mod"
    sa_sig_mod = create_shared_array(sa_sig_name_mod, 30, np.uint64)
    sa_sig_mod

    sa_sig_name_snk = init_ticks_model["modules"]["init_sink"]["out"]["args"][
        "sig_name"
    ]
    sa_sig_snk = create_shared_array(sa_sig_name_snk, 30, np.uint64)

    # run LiCoRICE
    licorice.go(
        init_ticks_model,
        confirm=True,
        working_path=f"{pytest.test_dir}/module_code/test_init",
        template_path=f"{pytest.test_dir}/templates",
    )

    sa.delete(sa_sig_name_in)
    sa.delete(sa_sig_name_src)
    sa.delete(sa_sig_name_mod)
    sa.delete(sa_sig_name_snk)

    validate_model_output(capfd, NUM_TICKS)

    # asert source output is sequential for all ticks
    for i in range(1, TOTAL_TICKS):
        assert sa_sig_src[i] - sa_sig_src[i - 1] == 1

    # assert module output is sequential for all ticks less source init
    for i in range(1, TOTAL_TICKS - SRC_INIT_TICKS):
        assert sa_sig_mod[i] - sa_sig_mod[i - 1] == 1
    for i in range(TOTAL_TICKS - SRC_INIT_TICKS, TOTAL_TICKS):
        assert sa_sig_mod[i] == 0

    # assert sink output is sequential for running ticks
    for i in range(1, TOTAL_TICKS - SRC_INIT_TICKS - MOD_INIT_TICKS):
        assert sa_sig_snk[i] - sa_sig_snk[i - 1] == 1
    for i in range(TOTAL_TICKS - SRC_INIT_TICKS - MOD_INIT_TICKS, TOTAL_TICKS):
        assert sa_sig_snk[i] == 0
