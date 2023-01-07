import glob
import os
import sys
from distutils.sysconfig import get_python_lib

import numpy as np


def test_numpy_using_blas_lapack():
    assert np.__config__.get_info("openblas64__info")
    assert np.__config__.get_info("openblas64__lapack_info")

    so_loc = glob.glob(
        f"{get_python_lib()}" "/numpy/core/_multiarray_umath.cpython-*"
    )[0]
    if sys.platform.startswith("linux"):
        stream = os.popen(f"ldd {so_loc}")
    elif sys.platform.startswith("darwin"):
        stream = os.popen(f"otool -L {so_loc}")
    else:
        raise NotImplementedError("System platform not supported.")

    output = stream.read()
    assert "libopenblas" in output
