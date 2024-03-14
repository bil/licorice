#!/bin/bash
set -ev

# This script installs LiCoRICE system and Python dependencies.

# pyenv-recommended python dependencies:
# https://github.com/pyenv/pyenv/wiki#suggested-build-environment

# By default, dependencies are updated.
SKIP_DEPS=${LICO_SKIP_DEPS:-0}

# By default, Python dependencies are not force reinstalled.
# Set `LICO_FORCE_REINSTALL_VENV` to override this behavior
FORCE_REINSTALL_VENV=${LICO_FORCE_REINSTALL_VENV:-0}

# install platform-specific packages
if [ $SKIP_DEPS -eq 0 ] ; then
    case $OSTYPE in
        linux*)
            if [ -f "/etc/debian_version" ]; then
                sudo apt-get update
                sudo apt-get install -y make build-essential libssl-dev \
                    zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget \
                    curl llvm libncursesw5-dev xz-utils tk-dev libxml2-dev \
                    libxmlsec1-dev libffi-dev liblzma-dev # python deps
                sudo apt-get install -y libopenblas-base libopenblas-dev sqlite3 \
                    libmsgpack-dev libevent-dev libasound2-dev gfortran
            else
                echo "Automatic dependency installation not supported for your " \
                     "flavor of Linux. Please install dependencies manually."
            fi
            ;;
        darwin*)
            if [ xcode-select -p > /dev/null 2>&1 ]; then
                echo "Installing XCode CLI. This may take a while...\n"
                xcode-select --install
            fi
            if [ which brew  > /dev/null 2>&1 ]; then
                echo "Installing Homebrew. This may take a while...\n"
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/" \
                                            "Homebrew/install/HEAD/install.sh)"
            fi
            brew install openssl readline sqlite3 xz zlib tcl-tk # python deps
            brew install openblas msgpack libevent
            ;;
        *)
            echo "Automatic dependency installation not supported for your OS." \
                 "Please install dependencies manually."
            exit 1
            ;;
    esac
fi

# install pyenv
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
if [ ! "$(pyenv --version)" ] ; then
    curl https://pyenv.run | bash
    source "$(dirname "$0")/pyenv_config.sh"
fi

# install python using pyenv, create a virtualenv, and install python deps
if [ $FORCE_REINSTALL_VENV -eq 1 ]; then
    PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install 3.8.12 -f
    pyenv uninstall -f licorice
    pyenv virtualenv -f 3.8.12 licorice
else
    PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install 3.8.12 -s
    if [ "$(pyenv version-name)" != "licorice" ]; then
        pyenv virtualenv 3.8.12 licorice
    fi

fi
"$(dirname "$0")/update-deps.sh"

# install pre-commit hooks
exec $SHELL
pre-commit install
