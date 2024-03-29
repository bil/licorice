*******************************************************************************
Packaging
*******************************************************************************


PyPI
===============================================================================

Cutting PyPI releases is done automatically when a tag pipeline runs in Gitlab
CI. From the repo's default branch, update the version number in ``setup.py`` and
run:

.. code-block:: bash

    ./packaging/release_pypi.sh


Binary
===============================================================================

A standalone executable of licorice can be created by running the script:

.. code-block:: bash

    ./packaging/create_binary.sh

This will create a portable executable `dist/licorice`.

If the created executable `dist/licorice` is experiencing issues, first try building a single directory executable and debugging that:

.. code-block:: bash

    ./packaging/create_binary.sh licorice_onedir.spec


This will create a portable folder ``dist/licorice`` that contains an executable `licorice`

