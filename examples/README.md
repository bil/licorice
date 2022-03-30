# LiCoRICE examples

This directory contains examples on how to use LiCoRICE.

## Directory structure

This examples directory is laid out similarly to how it might be used in a deployed system.

We recommend creating a directory structure in the following manner:

* `rig`
  * `models` (directory where the YAML files specifying the various LiCoRICE models)
  * `modules` (directory where the code for the various LiCoRICE modules is kept)
  * `run` (output directory where the code and compiled binaries of the LiCoRICE model is output to)

This is LiCoRICE's default behavior, but may be overrided by setting the LICORICE_*_DIR environment variables as described in the top-level README.

## Example models

To use these examples, `cd` into this directory after installing `licorice` or set the `LICORICE_WORKING_DIR` environment variable to the location of the `examples/` directory on your system.

These demos are listed in order of increasing model feature complexity.
If a specific demo does not work, it is advised to try a less complex one to assist with debugging.

### jitter\_demo

This is the simplest demo with no sources, modules, or sinks.
It is helpful to measure core timing performance of the operating system (e.g., validating the realtime kernel).

After following the instructions above, the model can be executed with the following command:

`licorice_go models/jitter_demo`

An oscilloscope tapping pin 9 of the parallel port should show a square wave with a 2ms period on 3.3V or 5V rails.

### parallel\_toggle

The `parallel_toggle` model is like the `jitter_demo`, but leverages the platform infrastructure.
It implements a simple model that again toggles an output pin of the parallel port every tick (default ticks are 1ms).

### matrix\_multiply

The `matrix_multiply` model demonstrates `numba.pycc` BLAS optimized numerical operations.

The `matmul` module performs matrix multiplication on two 4x4 matrices.

### logger\_demo

The `logger_demo` model demonstrates the SQLite signal (data) logging features of the platform.

### joystick\_demo

The `joystick_demo` model demonstrates how to bring two axes from a USB joystick in as inputs to the system.
This model requires the compilation of a realtime USB kernel (see the `kernel_setup_usb.sh` script in the install directory) and requires pygame for joystick control.
Install pygame into the venv via `pip install pygame`.

Any USB joystick device will work so long as pygame detects a joystick with at least two analog axes.
An example verified working joystick is the Logitech F310 Gamepad.

### pygame\_demo

The `pygame_demo` model demonstrates a simple SDL-driven sprite output to the screen.

This model requires the X window system and appropriate SDL drivers.
The `vis_pygame_setup.sh` script in the install directory will install the necessary packages.

This model must be launched from a running X session.
An example `.xinitrc` file to use with `startx` is provided in the install directory.
Move this sample `.xinitrc` to the home directory and then call `startx`.
Then repeat the steps from the main README to source the venv and source `licorice_activate.sh`.

### cursor\_track

The `cursor_track` model demonstrates a simple closed loop model where the input of two axes of a USB joystick are read and used to control a cursor on the screen using pygame.
It is recommended that this model be run only after `joystick_demo` and `pygame_demo` have been confirmed working.

### pinball\_demo

The `pinball_demo` model combines several of the features of the prior demos into a simple random target acquisition task, often referred to as a "pinball task" in the literature.
A USB joystick is again used an input to control a cursor that is displayed on the screen through pygame.
A green target is randomly placed on the screen and must be acquired and held with the cursor within an allotted time.
Relevant model signals are saved into the SQLite database by the datalogger.
