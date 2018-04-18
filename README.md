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

* rig
  * licorice (this is the licorice repository here)
  * models (directory where the YAML files specifying the various LiCoRICE models)
  * modules (directory where the code for the various LiCoRICE modules is kept)
  * run (output directory where the code and compiled binaries of the LiCoRICE model is output to)

### Installation 

1. Clone the LiCoRICE repository and place it in the directory structure as mentioend above

2. Compile realtime kernel

   From the top-level LiCoRICE directory, run:

    ```
    ./docs/rt_kernel_setup.sh
    ```

   This script will take one to two hours to complete.
   Reboot to finish installation when notified.
   A USB keyboard will not work after this point (USB support is disabled in this realtime kernel), use a PS/2 keyboard or ssh into the system.

3. Python virtualenv setup

   From the top-level LiCoRICE directory, run:
    ```
    ./docs/venv_setup.sh
    ```

   This script will take 15 to 30 minutes to complete.

4. Bind to the virtualenv:

    ```
    source ~/venv/bin/activate
    ```

5. Source the LiCoRICE aliases:

    ```
    source ~/LiCoRICE/.bash_aliases
    ```
