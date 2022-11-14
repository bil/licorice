******************************************************************************
Installation
******************************************************************************

#. Install with pip. We recommend using a `virtual environment <https://docs.python.org/3/library/venv.html>`_ (`pyenv <https://github.com/pyenv/pyenv-installer>`_, `conda <https://docs.conda.io/projects/conda/en/latest/>`_):

    .. code-block:: bash

        pip install licorice


#. To install the latest development version of LiCoRICE, you can instead use:

    .. code-block:: bash

        pip install git+https://github.com/bil/licorice@main

#. Ensure Correct Permissions

    .. include:: partials/_permissions.rst

That's all for a basic install (soft realtime) of LiCoRICE!

Improve realtime timings
===============================================================================

If you have stricter timing needs, the following optional steps can be taken on Debian:


Option 1 (easy): ``linux-lowlatency``
-------------------------------------------------------------------------------

Install the `linux-lowlatency <https://launchpad.net/ubuntu/+source/linux-lowlatency>`_ package:

    .. code-block:: bash

        sudo apt-get install linux-lowlatency

This will install a new `lowlatency` kernel on your machine, so make sure you reboot and select the correct kernel from the boot menu. You can check which kernel you're using by running:

    .. code-block:: bash

        uname -r


Option 2 (advanced): custom kernel
-------------------------------------------------------------------------------

Modify BIOS settings and compile a custom realtime kernel:

    .. include:: partials/_rt_setup.rst

We do not currently offer guidance for achieving firmer realtime guarantees on systems other than Debian, but contributions and testing are very welcome!
