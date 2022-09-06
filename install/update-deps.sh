#!/bin/bash


cd $(dirname "$0") # script always runs from install directory

eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

pyenv activate licorice

# numba requires setuptools<60
pip install --upgrade pip "setuptools<60"
pip install wheel pip-tools

pip-compile "./requirements.in"
pip-compile "./requirements-dev.in"

case $OSTYPE in
    linux*)
        pip-compile "./linux-requirements.in"
        pip-sync "./requirements.txt" "./requirements-dev.txt" "./linux-requirements.txt"
        ;;

    *)
        pip-sync "./requirements.txt" "./requirements-dev.txt"
        ;;
esac
