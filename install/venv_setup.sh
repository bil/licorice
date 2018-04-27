#!/bin/bash

# this will setup the base packages and venv necessary to make the LiCoRICE system work
# this should be performed after the realtime kernel is installed

NUM_CPUS=`grep processor /proc/cpuinfo|wc -l`

TMP=/tmp
SRC_NUMPY=$TMP/numpy
SRC_SCIPY=$TMP/scipy

VENV_DIR=~/lico_venv


# install some packages
sudo apt-get -y install libpython-dev python-virtualenv libopenblas-base libopenblas-dev sqlite libsqlite3-dev libevent-dev htop

# make venv
virtualenv -p python2 $VENV_DIR
source $VENV_DIR/bin/activate

# install cython
pip install cython

# compile numpy
git clone https://github.com/numpy/numpy $SRC_NUMPY
cd $SRC_NUMPY
git checkout tags/v1.14.2 -b v1.14.2
python setup.py build -j $NUM_CPUS
pip install .

# compile scipy
git clone https://github.com/scipy/scipy $SRC_SCIPY
cd $SRC_SCIPY
git checkout tags/v1.0.1 -b v1.0.1
python setup.py build -j $NUM_CPUS
python setup.py install

# install remaining python packages from pip
pip install argparse pyyaml jinja2 toposort psutil portio sharedarray==2.0.4 matplotlib numba
