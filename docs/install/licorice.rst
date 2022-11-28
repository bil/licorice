******************************************************************************
Installation
******************************************************************************

.. toctree::
       :hidden:

       python.rst

#. :ref:`Install Python and use a virtualenv <install/python:Installing Python and virtualenv>`.


#. Install LiCoRICE dependencies for Debian:

    .. code-block:: bash

        sudo apt update
        sudo apt install -y libevent-dev libsqlite3-dev libmsgpack-dev libopenblas-base libopenblas-dev gfortran sqlite3

    Or Mac using `Homebrew <https://brew.sh/>`_:

    .. code-block:: bash

        brew install openblas msgpack libevent


#. Install LiCoRICE using pip. Make sure the virtualenv you created in step 1 is activated:

    .. code-block:: bash

        pip install licorice


#. To install the latest development version of LiCoRICE, you can instead use:

    .. code-block:: bash

        pip install git+https://github.com/bil/lico-dev@main

#. Ensure Correct Permissions

    .. include:: /partials/_permissions.rst

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

    .. include:: /partials/_rt_setup.rst

We do not currently offer guidance for achieving firmer realtime guarantees on systems other than Debian, but contributions and testing are very welcome!
