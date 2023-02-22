*******************************************************************************
Directory Structure
*******************************************************************************

We recommend creating a directory structure to house your LiCoRICE models in the following manner:

.. code::

  licorice_workspace
  └──model_1
  │  │  model_1.yaml (YAML file specifying the given LiCoRICE model)
  │  │  model_1_module.py (user code for a `model_1` module)
  │  │  model_1_module_constructor.py (user code for a `model_1` module
  │  │    constructor)
  │
  └──model_2
  │  │  model_2.yaml
  │  │  model_2_source.c
  │  │  model_2_source_constructor.c
  │  │  model_2_source_destructor.c
  │  │  model_2_module.py
  │
  └──shared_modules
     │  shared_module.py
     │  shared_module_constructor.py

This is LiCoRICE's default behavior and may be overrided by setting the ``LICORICE_*_PATH`` and ``LICORICE_*_DIR`` :ref:`environment variables <api/env_vars:Environment Variables>`.
