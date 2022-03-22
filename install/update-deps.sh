#!/bin/sh

eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

pyenv activate licorice

pip install --upgrade pip setuptools
pip install wheel pip-tools

pip-compile "$@"
pip-sync requirements.txt
