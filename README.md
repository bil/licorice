## Artifact for "#55  WIP: An open-source realtime computational platform," LCTES 2018

LiCoRICE is an application layer that allows for soft realtime processing of data, but for reliable timing the application layer must be run on a machine that is properly configured and patched with the RTLinux kernel patch. This artifact provides necessary files and instructions to reproduce experiments from the LCTES 2018 paper by Mehrotra, Dasgupta, et al. from a clean install of Ubuntu 16.04 LTS.

## Hardware Prerequisites

LiCoRICE setup:
* x86_64 architectures supported
* other architectures supported by the PREEMPT_RT patch (untested)
* at least 2 CPU cores with hyperthreading (ideally 4 or more)

Tests: 
* 2 identical LiCoRICE setups
* 2 parallel ports on each machine 
* 1- or 10- gigabit ethernet cards on both machines
* oscilloscope (to verify and visualize jitter and latency measurements during runtime)

## OS/Kernel Prequisities and Setup

Clone the LiCoRICE repository and patch the kernel. From the top-level LiCoRICE directory run:

```
/docs/rt_kernel_setup.sh
```

and reboot to finish installation.

## Software Prerequisites and Setup

Python:

First install numpy from source.
<!-- OR WITH ANACONDA/INTEL MKL? -->

Next, install scipy, cython, and numba from source. 
<!-- DO WE NEED TO DETAIL THIS? -->

Finally, install the remaining dependencies with pip:

```
pip install argparse yaml jinja2 toposort psutil literal_eval portio SharedArray
```

Install sqlite3 and matplotlib:

```
$ sudo apt-get install sqlite3 libsqlite3-dev python-matplotlib
```

Add the following to your.bashrc file:

```
if [ -f ~/LiCoRICE/.bash_aliases ]; then
    . ~/LiCoRICE/.bash_aliases
fi
```

and reload your bashrc:
```
$ source ~/.bashrc
```

## Running the System

```
$ r throughput_test.yaml
```

## Tests

To get parallel port base numbers:

```
$ cat /proc/ioports | grep parport
```

Run all tests starting from the LiCoRICE base directory. Jitter and throughput tests require two realtime computers as set up above.

* System Start Time:

```
$ cd lico_tests
$ ./systemStartTime.sh N
```

where the output is the average system start time over N tests in ns

* Throughput


First, open templating/throughput_test.yaml and set the IP addresses of eth_in and eth_out to match the local machine's IP address and the second machine's IP address, respectively. Feel free to change the ports as well.

Then, open lico_tests/throughput_writer.c and change the IP and port to match that of eth_in as set above. 

On system 1 (LiCoRICE):

```
$ r throughput_test.yaml
```

On system 2 (data generation)

```
$ test_thru
```

* Jitter

Connect systems 1 and 2 by parallel port. To view signals on an oscilloscope, use a parallel port breakout board and connect any of the data pins (2-9). Any of pins 18-25 are ground.

On system 1 (LiCoRICE):

Open templating/throughput_test.yaml and replace config/parport_tick_addr with the  parallel port base address sending ticks to system 1.

Run LiCoRICE:

```
$ r throughput_test.yaml
```

On system 2 (tick measurement):

Open lico_tests/jitter_det.c and replace PARA_PORT_BASE_ADDR with the parallel port base address receiving ticks from system 2.

Run the tick recorder:

```
$ test_jit
```

To plot the data as a histogram, run:

```
python jitter.py
```

from the lico_tests/ directory.

The jitter test may also be run while system 2 is sending data to system 1 over ethernet as in the throughput test.

* Latency

Connect systems 1 and 2 with two separate parallel port male to male cables. Results can be viewed on an oscilloscope as detailed above.

On system 1 (LiCoRICE):

Open templating/latency_par_test.yaml, replace par_in/args/addr with the parallel port base address reading in from system 2 and replace par_out/args/addr with the parallel port base address writing to system 2.

```
$ r latency_par_test.yaml
```

On system 2 (tick send and measurement):

Open lico_tests/latency_par_writer.c and replace PARA_PORT_BASE_ADDR with the parallel port base address writing to system 1. Open lico_tests/jitter_det.c and replace PARA_PORT_BASE_ADDR with the parallel port base address reading from system 1.

On first bash shell:

```
test_lat1
```

On second bash shell:

```
test_lat2
```

* CPU Crunch

```
$ r numba_burn_test.yaml
```

## Interpreting Results

TODO: put in python file used to graph stuff