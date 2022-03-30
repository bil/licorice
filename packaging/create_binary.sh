#!/bin/bash

eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

pyenv activate licorice

SPEC_FILE="${1:-licorice_onefile.spec}"
echo $SPEC_FILE

pyinstaller "$(dirname "$(which "$0")")/$SPEC_FILE" -y
