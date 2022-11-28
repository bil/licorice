******************************************************************************
LiCoRICE Examples
******************************************************************************

The ``examples/`` directory contains examples on how to use LiCoRICE. Please follow :ref:`instructions for installing LiCoRICE <install/licorice:Installation>` first.


Directory structure
===============================================================================

The ``examples/`` directory is laid out similarly to how it might be used in a deployed system.

We recommend creating a directory structure in the following manner:

* model_1

  - model_1.yaml (YAML file specifying the given LiCoRICE model)
  - model_1_module.py (user code for a `model_1` module)
  - model_1_module_constructor.py (user code for a `model_1` module constructor)

* model_2

  - model_2.yaml
  - model_2_source.c
  - model_2_source_constructor.c
  - model_2_source_destructor.c
  - model_2_module.py

* shared_modules

  - shared_module.py
  - shared_module_constructor.py

This is LiCoRICE's default behavior, but may be overrided by setting the ``LICORICE_*_PATH`` and ``LICORICE_*_DIR`` :ref:`environment variables <api/env_vars:Environment Variables>`.


Example models
===============================================================================

To use these examples, simply run ``./examples/<example_name>/run.sh`` from the licorice repository root directory. Setting of the correct LICORICE_* environment variables is handled by the run scripts, so please take a look at how those work if you're curious.

These demos are listed in order of increasing model feature complexity.
If a specific demo does not work, it is advised to try a less complex one to assist with debugging.


jitter
-------------------------------------------------------------------------------

This is the simplest demo with no sources, modules, or sinks.
It is helpful to measure core timing performance of the operating system (e.g., validating the realtime kernel).

This example requires the use of a parallel port. We recommend a PCIe parallel port adapter compatible with Linux. Make sure your parallel port drivers are working and that the port is listed under ``/dev/parport<index>``. Then, make sure the user running LiCoRICE can access the port by adding them to the ``lp`` group as follows:

  .. code-block:: bash

    sudo usermod -aG lp <user>

Then log out and back in for the changes to take effect.


After installing LiCoRICE, the model can be executed with the following command:

  .. code-block:: bash

    examples/jitter/run.sh

An oscilloscope tapping pin 9 of the parallel port should show a square wave with a 2ms period on 3.3V or 5V rails.


parallel_toggle
-------------------------------------------------------------------------------

The ``parallel_toggle`` model is like the ``jitter_demo``, but leverages the platform infrastructure.
It implements a simple model that again toggles an output pin of the parallel port every tick (default ticks are 1ms).
Make sure the above jitter example works before running this example.


matrix_multiply
-------------------------------------------------------------------------------

The ``matrix_multiply`` model demonstrates ``numba.pycc`` BLAS optimized numerical operations.

The `matmul` module performs matrix multiplication on two 4x4 matrices.


logger
-------------------------------------------------------------------------------

The ``logger`` model demonstrates the SQLite signal (data) logging features of the platform.


joystick
-------------------------------------------------------------------------------

The ``joystick`` model demonstrates how to bring two axes from a USB joystick in as inputs to the system.
This model requires the compilation of a realtime USB kernel (see the `kernel_setup_usb.sh` script in the install directory) and requires pygame for joystick control.
Install pygame into the venv via ``pip install pygame``.

Any USB joystick device will work so long as pygame detects a joystick with at least two analog axes.
An example verified working joystick is the Logitech F310 Gamepad.


pygame
-------------------------------------------------------------------------------

The ``pygame`` model demonstrates a simple SDL-driven sprite output to the screen.

This model requires the X window system and appropriate SDL drivers.
The ``vis_pygame_setup.sh`` script in the install directory will install the necessary packages.

This model must be launched from a running X session.
An example ``.xinitrc`` file to use with ``startx`` is provided in the install directory.
Move this sample ``.xinitrc`` to the home directory and then call ``startx``.
Then repeat the steps from the main README to source the venv and source ``licorice_activate.sh``.


cursor_track
-------------------------------------------------------------------------------

The ``cursor_track`` model demonstrates a simple closed loop model where the input of two axes of a USB joystick are read and used to control a cursor on the screen using pygame.
It is recommended that this model be run only after ``joystick`` and ``pygame`` have been confirmed working.


pinball
-------------------------------------------------------------------------------

The ``pinball`` model combines several of the features of the prior demos into a simple random target acquisition task, often referred to as a "pinball task" in the literature.
A USB joystick is again used an input to control a cursor that is displayed on the screen through pygame.
A green target is randomly placed on the screen and must be acquired and held with the cursor within an allotted time.
Relevant model signals are saved into the SQLite database by the datalogger.
