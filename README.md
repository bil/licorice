# LiCoRICE - Linux Comodular Realtime Interactive Computation Engine

LiCoRICE is an open-source computational platform implementing a model-based design for **real-time** processing of streaming data.

It facilitates the execution of numerical operations in [python](https://www.python.org) with empirical real-time guarantees, supports storage of streaming data to an [SQLite Database](https://www.sqlite.org/index.html), and supports USB peripherals and output to a display([pygame](https://www.pygame.org/wiki/about)), all while maintaining at least 1ms ticks.

LiCoRICE was developed in the Stanford Brain Interfacing Laboratory, where it is currently used to control and conduct closed-loop neuroscience experiments.

#### Why Realtime

While typical data analysis will collect data and then processes it in batches, real-time processing is the immediate analysis of data as it is collected, allowing for near-instantaneous response and up-to-date outputs. There are a large number of systems that depend on real-time analysis as milliseconds of delay can make an immense difference, whether it be conducting closed loop experiment or trading stocks.

#### Why Licorice

Although real-time computational platforms do exist, many of them are either expensive and/or restrictive. The open-source nature of LiCoRICE forgoes both of these problems allowing for anyone to download, install, and adapt licorice to any system or use case.

## System Prerequisites

* x86\_64 system
* Modern UNIX environment (Linux, MacOS)
* Python 3.6+
* GCC toolchain

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
  * `run` (LiCoRICE-managed output directory where populated code templates, compiled binaries, and data files for the LiCoRICE model are to)

However, this directory structure is completely configurable. Users should set `LICORICE_WORKING_PATH` to the experiment root (`rig` above). Each experiment subdirectory may also be set individually with `LICORICE_MODULE_PATH`, `LICORICE_OUTPUT_DIR`, `LICORICE_EXPORT_DIR`, `LICORICE_TMP_MODULE_DIR` , and `LICORICE_TMP_OUTPUT_DIR`. Setting any of these will override the default `LICORICE_WORKING_DIR/<subdirectory>`. If `LICORICE_WORKING_PATH` is not set, LiCoRICE will set it to the current working directory and issue a warning. To search for files in multiple directories, LiCoRICE`*_PATH` environment variables support BASH-like lists of paths separated by your OS'es path separator (commonly `:` for Linux).


## Installation

1. Clone the LiCoRICE repository.

1. Python virtualenv setup

    From the top-level LiCoRICE directory, run:

    ```bash
    ./install/env_setup.sh
    ```

    This script will take 15 to 30 minutes to complete.

1. [Install pyenv and pyenv-virtualenv in your shell config.](https://github.com/pyenv/pyenv#set-up-your-shell-environment-for-pyenv) Bash users can use the following:

    ```bash
    cat ./install/pyenv_config.sh >> ~/.bashrc
    if [ -f "~/.bash_profile" ]; then
      cat ./install/pyenv_config.sh >> ~/.bash_profile
    else
      cat ./install/pyenv_config.sh >> ~/.profile
    fi
    source ~/.bashrc
    ```

1. Bind to the newly built virtualenv:

    ```bash
    pyenv activate licorice
    ```

    Or alternatively include a `.python-version` file in the top-level LiCoRICE directory with the single line:

    ```
    licorice
    ```



1. Ensure Permissions and Paths

    To ensure you have the correct permissions, create a new limits file with ```sudo vi /etc/security/limits.d/licorice.conf ``` and add these lines to ensure your user can run licorice. _Replace `user` with the user you are using to run licorice_.

    ```bash
    user - rtprio 95
    user - memlock unlimited
    ```

    Now log out and back in and you are set up for non-realtime licorice development and usage!

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

### Darwin

If issues with Numpy arise, it may be necessary to put `export OPENBLAS=$(brew --prefix openblas)` in your `~/.bashrc` or similar.
arise

## Examples

The examples folder contains instructions on how to get started with LiCoRICE.

It is recommended that first-time users work through the examples to become familiar with the basics of the LiCoRICE workflow.

## Usage

In general, only one command needs to be issued to parse, compile, and run a model:

```bash
licorice go <model_name>
```

For more advanced usage, take a look at the docs.

