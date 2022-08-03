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


### Installation 

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

1. Install LiCoRICE locally

    ```bash
    pip install -e .
    ```

    This will add a shell command called `licorice` which is the single entrypoint into the LiCoRICE application.

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

## Models

Models define the architecture of your real-time analysis pipeline from data acquisition(sources) to processing(modules) to output(sinks). Models are defined through [yaml](https://www.cloudbees.com/blog/yaml-tutorial-everything-you-need-get-started) files and have three primary keys:

##### Config

Here we define aspects of the setup, timing, and ticks(our metric of time) in order to control the way our system interacts with the real world.

| Keyword          | Usage                                                        |
| ---------------- | :----------------------------------------------------------- |
| tick_size        | Set the time per tick in nanoseconds                         |
| num_ticks        | The number of ticks to run the model for                     |
| init_tick_buffer | The number of ticks to run before modules start reading data from the source |

##### Signals

Here we define how data will be passed between our modules. We also define how much of this data to keep over time and how to store it if necessary for our use case. At a high-level, signals are represented as NumPy arrays in our modules. However, in implementation, they are actually shared arrays, shared memory that allows for the fast transfer of data between models required for real-time analysis. 
| Keyword     | Usage                                                        |
| ----------- | ------------------------------------------------------------ |
| shape       | The shape of the incoming data as a NumPy array              |
| dtype       | The type of the data                                         |
| history     | How many ticks worth of data to keep                         |
| log         | Whether or not to log the signal                             |
| log_storage | Specifications for how to log the data (see examples for details) |

##### Modules 

Modules are the primary building blocks of licorice. Here we define the name of our module, the language it's in (python or C), what signals, if any, will be streaming in, and what signals, if any, will be streaming out. We also define whether this module will use a parser to read or write external signals, a constructor to prepare data or initialize processes, or a destructor to stop processes or clean data.

| Keyword     | Usage                                                        |
| ----------- | ------------------------------------------------------------ |
| Language    | The programming language used to write the module(Python or C) |
| Constructor | Indicates that a constructor is used to initialize the module |
| Parser      | Indicates that a parser is used to read data from an external source |
| Destructor  | Indicates that a destructor is used to correctly breakdown a module |
| In          | Under this key, you define each of your inputs for this module |
| Out         | Under this key, you define each of your outputs for this module |

###### External Signals

External signals are information that is passed in and out of our model. Having an external signal is what defines modules as either a sink or a source(any module should only ever have one). Given the inherent complexity of dealing with external devices or applications, additional information is needed to define these signals.

_Coming Soon_

```yaml
# Example Model
config:

  tick_size: 100000 # This is equicalent to 1ms
  num_ticks: 10 # How many ticks to run for
  
signals:
  
  signal_1:
    shape: (2, 2) # All signals are should be treated as numpy arrays
    dtype: float64
    history: 1 # How much previous data to keep on the signal in the system
    
   signal_2:
   	shape: 1 # Signals can also be 1D
   	dtype: float64
   	
modules:

  sum_init:
      language: python  # can be C or python
      constructor: True. # signifies we will use a constructor
      in:	# An External Signal(Joystick in USB)
      	name: jdev
      	args:
      		type: usb_input
      	schema:
      		packets_per_ticket: 1
      		data:
      			dtype: double
      			size: 2
      out:
        - signal_1
			
	sum:
		language: python
		in:
			- signal_1
		out:
			- signal_2
			
	sum_print:
		language: python
		in:
		  - signal_2
```

## Examples

The examples folder contains instructions on how to get started with LiCoRICE.

It is recommended that first-time users work through the examples to become familiar with the basics of the LiCoRICE workflow.

## Usage

TODO: expand this section

In general, only one command needs to be issued to parse, compile, and run a model:

```bash
licorice go <model_name>
```

This performs the following actions:

1. Parsing

    Once a LiCoRICE model is configured, it must be parsed to generate the code.
    This is done with the following command and assumes that the shell is bound to the virtualenv:

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

