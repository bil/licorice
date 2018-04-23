# LiCoRICE examples

This directory contains examples on how to use LiCoRICE.

## Directory structure

This examples directory is laid out similarly to how it would be used in a deployed system.
Note that this directory structure must be placed *OUTSIDE* the LiCoRICE repository.
Simiarly, this directory does not contain a licorice repository, which is necessary for function.

As a reminder, construct the directory structure in the following manner:

* `rig`
  * `licorice` (this is the LiCoRICE git repository)
  * `models` (directory where the YAML files specifying the various LiCoRICE models)
  * `modules` (directory where the code for the various LiCoRICE modules is kept)
  * `run` (output directory where the code and compiled binaries of the LiCoRICE model is output to)

## Example models

### parallel\_toggle

The `parallel_toggle` model is a simple example that toggles an output pin of the parallel port every tick (default ticks are 1ms).

Once the directory structure is in place and the environments have been properly bound, the model can be executed with the following command:

`licorice_go parallel_toggle`

An oscilloscope tapping pin 9 of the parallel port should show a square wave with a 2ms period on 3.3V or 5V rails.
