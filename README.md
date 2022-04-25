# LiCoRICE - Linux Comodular Realtime Interactive Computation Engine

LiCoRICE is a platform that performs realtime processing of data.
It is suitable for numerical processing of streaming data into and through a system.

## System Prerequisites

* x86\_64 system
* Modern UNIX environment (Linux, MacOS)
* Python (both Python 2 and 3 are supported)
* gcc toolchain

**NOTE**: The setup scripts here are currently only tested on Ubuntu 20.04.4 LTS (Focal Fossa).
We recommend starting with a stock install of Ubuntu Server 20.04 LTS.
Use of any other UNIX platform requires manual installation of packages.

## Setup

### Directory structure

LiCoRICE is designed to be a standalone application that operates on a separate repository.
This repository is where the configuration, code, and binaries for the models that LiCoRICE runs are stored.
An example directory structure for an experimental rig might contain:

* `rig`
  * `models` (directory where the YAML files specifying the various LiCoRICE models)
  * `modules` (directory where the code for the various LiCoRICE modules is kept)
  * `run` (output directory where the code and compiled binaries of the LiCoRICE model is output to)

However, this directory structure is completely configurable. Users should set `LICORICE_WORKING_DIR` to the experiment root (`rig` above). Each experiment subdirectory may also be set individually with `LICORICE_MODULE_DIR`, `LICORICE_OUTPUT_DIR`, `LICORICE_EXPORT_DIR`, `LICORICE_TMP_MODULE_DIR` , and L`ICORICE_TMP_OUTPUT_DIR`. Setting any of these will override the default LICORICE_WORKING_DIR/<subdirectory>. If LICORICE_WORKING_DIR is not set, LiCoRICE will use the current working directory as the rig and issue a warning.


### Installation 

1. Clone the LiCoRICE repository.

1. Python virtualenv setup

    From the top-level LiCoRICE directory, run:

    ```bash
    ./install/env_setup.sh
    ```

    This script will take 15 to 30 minutes to complete.

1. Bind to the newly built virtualenv:

    ```bash
    pyenv activate licorice
    ```

1. Install LiCoRICE locally

    ```bash
    pip install -e .
    ```

    This will add a shell command called `licorice` which is the single entrypoint into the LiCoRICE application.

1. Optional - Modify BIOS settings and compile realtime kernel

    1. Disable all USB and ACPI support in the BIOS of the target system

    USB and ACPI features throw CPU interrupts which can interfere with realtime performance.

    If USB support is needed for peripherals, enable only the minimum USB version necessary on as few ports as possible if such options in the BIOS exist.

    2. Compiling a realtime kernel is not a requirement to run LiCoRICE, but realtime performance is one of the central features of the platform.
    Without a realtime kernel, timing assurances are harder to deliver.
    Tick violations are more likely to occur as model complexity grows.
    For basic platform testing and evaluation, a realtime kernel is not necessary, but for any production deployments, realtime kernel compilation is strongly advised.

    The instructions for realtime kernel compilation here should be applied to a stock install of Ubuntu server 20.04 LTS.

    From the top-level LiCoRICE repository directory, run:

    ```bash
    ./install/kernel_setup.sh
    ```

    This script will take from one to five hours to complete, depeding on the speed and processor count of the system.
    Reboot to finish installation when notified.
    Any USB keyboards will not work after this point (USB support is disabled in this realtime kernel), use a PS/2 keyboard or ssh into the system.

    Note: if USB support is necessary (e.g., system requires realtime support for a USB peripheral), install the USB enabled kernel instead via `./install/kernel_setup_usb.sh` instead. Enabling USB support will degrade system performance by a small amount, but may still fit within application tolerances. In general, a limited number of USB devices do not preclude consistently meeting 1ms ticks. Regardless, it is important to always verify timings for a given system deployment.


## Examples

The examples folder contains instructions on how to get started with LiCoRICE.

It is recommended that first time users work through the examples to become familiar with the basics of the LiCoRICE workflow.

## Usage

TODO: expand this section

In general, only one command needs to be issued to parse, compile, and run a model:

```bash
licorice go <model_name>
```

This performs the following actions:

1. Parsing

    Once a LiCoRICE model is configured, it must be parsed to generate the code.
    This is done with the following command, and assumes that the shell is bound to the virtualenv:

    ```bash
    licorice parse <model_name>
    ```

2. Compiling

    Once parsed, the code is ready to be compiled.

    ```bash
    licorice compile <model_name>
    ```
3. Running

    After compilation, the model can then be run:
    ```bash
    licorice run <mode_name>
    ```

## Packaging

### PyPI

Cutting PyPI releases is done automatically when a tag pipeline runs in Gitlab
CI. From the repo's default branch, update the version number in `setup.py` and
run:

```bash
./packaging/release_pypi.sh
```

### Binary

A standalone executable of licorice can be created by running the script:

```bash
./packaging/create_binary.sh
````

This will create a portable executable `dist/licorice`.

If the created executable `dist/licorice` is experiencing issues, first try building a single directory executable and debugging that:

```bash
./packaging/create_binary.sh licorice_onedir.spec
```

This will create a portable folder `dist/licorice` that contains an executable `licorice`

