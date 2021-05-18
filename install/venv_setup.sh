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

# compile numpy
# git clone https://github.com/numpy/numpy $SRC_NUMPY
# cd $SRC_NUMPY
# git checkout tags/v1.14.2 -b v1.14.2 # try with most recent version or pip install numpy --no-binary
# python setup.py build -j $NUM_CPUS
# pip install .

# install cython
pip install cython

# install remaining python packages from pip
pip install numpy --no-binary numpy
pip install llvmlite
pip install scipy --no-binary scipy
pip install argparse
#pip install numpy==1.14.2
pip install cycler
pip install pyyaml
pip install sharedarray
pip install numba
pip install psutil
pip install portio
pip install matplotlib
pip install msgpack
pip install jinja2=2.11.3
pip install toposort
