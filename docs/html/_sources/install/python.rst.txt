:orphan:

******************************************************************************
Installing Python and virtualenv
******************************************************************************

We support a few different options for installing Python. The `install/env_setup.sh` script will install Python via pyenv as described below. Of course, you're welcome to use any other method that you prefer as well. We do recommend that you use a `virtual environment <https://docs.python.org/3/library/venv.html>`_ no matter how Python is installed.

Pyenv
===============================================================================

Use `Pyenv's automatic installer <https://github.com/pyenv/pyenv-installer>`_ for the simplest setup. Assuming you're using BASH with a ~/.bashrc file:

.. code-block:: bash

  curl https://pyenv.run | bash
  echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bashrc
  echo 'eval "$(pyenv init -)"' >> ~/.bashrc
  echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc
  exec $SHELL
  pyenv install 3.8.12

Then, create and activate a virtualenv for LiCoRICE using Pyenv:

.. code-block:: bash


  pyenv virtualenv 3.8.12 licorice
  pyenv activate licorice


Conda
===============================================================================

Install `conda <https://docs.conda.io/projects/conda/en/latest/>`_ by downloading the BASH installer and running it on your system. Once conda is installed, create and activate a virtualenv:

.. code-block::

  conda create -n licorice
  conda activate licorice

Note: conda installation is not yet tested.

System Python
===============================================================================

Install Python, create a virtualenv for licorice, and activate it:

Linux:

.. code-block:: bash

  sudo apt update
  sudo apt install -y python3-dev python3-venv
  python3 -m venv ~/.envs/licorice
  source ~/.envs/licorice/bin/activate

Mac:

.. code-block:: bash

  brew install python
  python m venv ~/.envs/licorice
  source ~/.envs/licorice/bin/activate
