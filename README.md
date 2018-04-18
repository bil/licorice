# LiCoRICE - Linux Comodular Realtime Interactive Computation Engine

LiCoRICE is an application layer that allows for soft realtime processing of data, but for reliable timing the application layer must be run on a machine that is properly configured and patched with the PREEMPT\_RT kernel patch.
The instructions here should be applied to a stock install of Ubuntu server 16.04 LTS.

## Hardware Prerequisites

LiCoRICE setup:
* x86\_64 system
* at least 2 CPU cores with hyperthreading (ideally 4 or more)

## Setup

### Directory structure

LiCoRICE is designed to be a submodule of a larger repository.
This larger repository is where the configuration, code, and binaries for the models that LiCoRICE are stored.
An example directory structure for an experimental rig would be:

* `rig`
  * `licorice` (this is the licorice repository here)
  * `models` (directory where the YAML files specifying the various LiCoRICE models)
  * `modules` (directory where the code for the various LiCoRICE modules is kept)
  * `run` (output directory where the code and compiled binaries of the LiCoRICE model is output to)

### Installation 

1. Clone the LiCoRICE repository and place it in the directory structure as mentioend above

2. Compile realtime kernel

    From the top-level LiCoRICE directory, run:

    ```bash
    ./docs/rt_kernel_setup.sh
    ```

    This script will take one to two hours to complete.
    Reboot to finish installation when notified.
    A USB keyboard will not work after this point (USB support is disabled in this realtime kernel), use a PS/2 keyboard or ssh into the system.

3. Python virtualenv setup

    From the top-level LiCoRICE directory, run:


    ```bash
    ./docs/venv_setup.sh
    ```

    This script will take 15 to 30 minutes to complete.

4. Bind to the virtualenv:

    ```bash
    source ~/venv/bin/activate
    ```

5. Source the LiCoRICE aliases:

    ```bash
    source ~/LiCoRICE/.bash_aliases
    ```

### Configuration

LiCoRICE needs a config YAML file that specifies paths.

An example config file appears below:
```yaml
paths :
  experiments : /home/bil/rig
  licorice : /home/bil/rig/licorice
```

The root of the `rig` directory is a good place to store this config file.

## Usage

1. Parsing

    Once a LiCoRICE model is configured, it must be parsed to generate the code.
    This is done with the following command, and assumes that the shell is bound to the virtualenv:

    ```bash
    python <path to LiCoRICE repository>/templating/lico_parse.py -c <path to LiCoRICE config file> -m <path to YAML model file to parse>
    ```

2. Compiling

    Once parsed, the code is ready to be compiled.
    Compiling is done in the `run/out` directory, where the output of the parsed code lives.

    ```bash
    make clean && make
    ```
3. Running

    After compilation, the model can be run via the following command:
    ```bash
    sudo PYTHONPATH=$VIRTUAL_ENV/lib/python2.7/site-packages taskset 0x1 nice -20 ./timer
    ```
