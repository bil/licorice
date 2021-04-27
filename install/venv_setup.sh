#!/bin/bash

# this will setup the base packages and venv necessary to make the LiCoRICE system work
#
# This should be run from inside the LiCoRICE repository directory

NUM_CPUS=`grep processor /proc/cpuinfo|wc -l`

TMP=/tmp
SRC_NUMPY=$TMP/numpy
SRC_SCIPY=$TMP/scipy

VENV_DIR=`pwd`/../venv

# install some packages
sudo apt-get -y install libpython-dev python-virtualenv libopenblas-base libopenblas-dev sqlite libmsgpack-dev libsqlite3-dev libevent-dev htop

# make venv
virtualenv -p python3.6m $VENV_DIR # change to python3.6m for python 3
source $VENV_DIR/bin/activate

# install cython
pip install cython==0.28

# install remaining python packages from pip
pip install argparse==1.4.0
pip install numpy==1.19.5
pip install argparse==1.4.0
pip install cycler==0.10.0
pip install pyyaml==5.4.1
pip install sharedarray==2.0.4
pip install numba==0.52.0
pip install psutil==5.8.0
pip install portio==0.5
pip install matplotlib==3.3.4
pip install msgpack==1.01
pip install jinja2==2.11.3
pip install toposort==1.6
