#!/bin/bash

# this will setup the base packages and venv necessary to make the LiCoRICE system work
#
# This should be run from inside the LiCoRICE repository directory

# install some packages
sudo apt-get -y install libopenblas-base libopenblas-dev sqlite libmsgpack-dev libsqlite3-dev libevent-dev htop

curl https://pyenv.run | bash

eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install 3.8.12 -f
pyenv virtualenv 3.8.12 licorice
./update-deps.sh
