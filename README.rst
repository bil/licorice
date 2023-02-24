###############################################################################
LiCoRICE - Linux Comodular Realtime Interactive Computation Engine
###############################################################################

LiCoRICE is an open-source computational platform implementing model-based design for **realtime** processing of streaming data.

It facilitates the execution of numerical operations in `python <https://www.python.org>`_ with empirical realtime guarantees, supports storage of streaming data to an `SQLite Database <https://www.sqlite.org/index.html>`_, and supports USB peripherals and output to a display via `pygame <https://www.pygame.org/wiki/about>`_, all while maintaining at least 1ms ticks.

LiCoRICE was developed in the `Stanford Brain Interfacing Laboratory <https://bil.stanford.edu/>`_, where it is currently used to control and conduct closed-loop neuroscience experiments.


*******************************************************************************
Motivation
*******************************************************************************

Why Realtime?
===============================================================================

While offline data analysis collects data and processes it in batches, realtime processing is the analysis of data as it is collected, allowing for predictable response time (latency) and minimal timing variation (jitter). Systems in which delays are consequential, such as conducting closed-loop experiments or high-frequency trading, can benefit from implementing realtime practices.

Why Licorice?
===============================================================================

Although realtime computational platforms do exist, many of them are inaccessible due to programming language, hardware, cost, or being proprietary. The high-level, POSIX-compliant, and open-source nature of LiCoRICE forgoes these problems and allows users to easily install LiCoRICE and adapt it to their use case.

*******************************************************************************
System Requirements
*******************************************************************************

* x86\_64 system
* Modern UNIX environment (Linux, MacOS)
* Python 3.6+
* GCC toolchain, libevent, SQLite3, and MessagePack

**NOTE**: Soft realtime timing guarantees are only currently tested for Ubuntu 20.04 LTS (Focal Fossa) and Ubuntu 18.04 LTS (Bionic Beaver).

We recommend starting with a stock install of Ubuntu Server 20.04 LTS.
Use of other UNIX platforms besides MacOS requires manual installation of packages.


*******************************************************************************
Installation
*******************************************************************************

LiCoRICE can be installed with pip, but requires some dependencies and permissions detailed in `the documentation <https://docs.licorice.su.domains/install/licorice.html>`_.

To achieve minimal jitter, it is recommended to install the stock ``linux-lowlatency`` kernel or a custom kernel. We provide a one-click setup script to install a suitable realtime kernel.

*******************************************************************************
User Guide
*******************************************************************************

LiCoRICE has `a growing user guide <https://docs.licorice.su.domains/guide/index.html>`_ which walks through creating some basic models from the ground up.


*******************************************************************************
Examples
*******************************************************************************

LiCoRICE also ships with `a number of examples <https://docs.licorice.su.domains/guide/examples.html>`_ that highlight its capabilities.

Some examples require external hardware to run.

*******************************************************************************
Usage
*******************************************************************************

In general, only one command needs to be issued to parse, compile, and run a model:

.. code-block:: bash

    licorice go <model_name>

For a more detailed description, take a look at the `API reference <https://docs.licorice.su.domains/api/index.html>`_.

