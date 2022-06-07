#!/bin/bash

eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

pyenv activate licorice

pip install --upgrade pip setuptools
pip install wheel pip-tools

pip-compile "$(dirname "$0")/requirements.in"
pip-compile "$(dirname "$0")/requirements-dev.in"

case $OSTYPE in
    linux*)
        pip-compile "$(dirname "$0")/linux-requirements.in"
        pip-sync "$(dirname "$0")/requirements.txt" "$(dirname "$0")/requirements-dev.txt" "$(dirname "$0")/linux-requirements.txt"
        ;;

    *)
        pip-sync "$(dirname "$0")/requirements.txt" "$(dirname "$0")/requirements-dev.txt"
        ;;
esac
