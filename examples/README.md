# LiCoRICE examples

This directory contains examples on how to use LiCoRICE.

## Directory structure

This examples directory is laid out similarly to how it would be used in a deployed system.
Note that this directory structure must be placed **OUTSIDE** the LiCoRICE repository and must **CONTAIN** a LiCoRICE repository.

As a reminder, construct the directory structure in the following manner:

* `rig`
  * `licorice` (this is the LiCoRICE git repository)
  * `models` (directory where the YAML files specifying the various LiCoRICE models)
  * `modules` (directory where the code for the various LiCoRICE modules is kept)
  * `run` (output directory where the code and compiled binaries of the LiCoRICE model is output to)

## Example models

To use these examples, copy the contents of the `models` and `modules` directories to the appropriate directories under the `rig` directory on the target LiCoRICE system.

### parallel\_toggle

The `parallel_toggle` model is a simple example that toggles an output pin of the parallel port every tick (default ticks are 1ms).

Once the directory structure is in place and the environments have been properly bound, the model can be executed with the following command:

`licorice_go parallel_toggle`

An oscilloscope tapping pin 9 of the parallel port should show a square wave with a 2ms period on 3.3V or 5V rails.

### matrix\_multiply

The `matrix_multiply` model demonstrates `numba.pycc` BLAS optimized numerical operations.

The `matmul` module performs matrix multiplication on two 4x4 matrices.

### joystick\_demo

The `joystick_demo` model demonstrates how to bring two axes from a USB joystick in as inputs to the system.
This model requires the compilation of a realtime usb kernel (see the `kernel_setup_usb.sh` script in the install directory).

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

The `cursor_track` model demonstrates a simple closed loop system where the input of two axes of a USB joystick are read and used to control a cursor on the screen using pygame. It is recommended that this model be run only after `joystick_demo` and `pygame_demo` have been confirmed working.
