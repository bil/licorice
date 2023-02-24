*******************************************************************************
Development Environment Setup
*******************************************************************************

#. Clone the LiCoRICE repository.

    .. code-block:: bash

            git clone https://github.com/bil/licorice.git
            cd licorice

    ..
        TODO use sphinx-tabs
        .. tabs::

            .. code-tab:: bash HTTPS

                git clone https://github.com/bil/licorice.git

            .. code-tab:: bash SSH

                git clone git@github.com:bil/licorice.git

            .. code-tab:: bash GitHub CLI

                gh repo clone bil/licorice


#. Python virtualenv setup

    From the top-level LiCoRICE directory, run:

    .. code-block:: bash

        ./install/env_setup.sh

#. `Install pyenv and pyenv-virtualenv in your shell config. <https://github.com/pyenv/pyenv#set-up-your-shell-environment-for-pyenv>`_ Bash users can use the following:

    .. code-block:: bash

        cat ./install/pyenv_config.sh >> ~/.bashrc
        if [ -f "~/.bash_profile" ]; then
          cat ./install/pyenv_config.sh >> ~/.bash_profile
        else
          cat ./install/pyenv_config.sh >> ~/.profile
        fi
        source ~/.bashrc

#. Bind to the newly built virtualenv:

    .. code-block:: bash

        pyenv activate licorice

    Or alternatively include a ``.python-version`` file in the top-level LiCoRICE directory containing ``licorice``:

    .. code-block::

        echo licorice > .python-version

#. Ensure Correct Permissions

    .. include:: ../partials/_permissions.rst

#. Optional - Modify BIOS settings and compile realtime kernel.

    .. include:: ../partials/_rt_setup.rst
