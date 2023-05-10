#!/bin/bash


cd $(dirname "$0") # script always runs from install directory

eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

pyenv activate licorice

pip install --upgrade pip setuptools wheel pip-tools

pip-compile "./requirements.in" --resolver=backtracking
pip-compile "./requirements-dev.in" --resolver=backtracking
pip-sync "./requirements.txt" "./requirements-dev.txt"
