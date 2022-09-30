###############################################################################
LiCoRICE CLI
###############################################################################

*******************************************************************************
Commands
*******************************************************************************

Generate
===============================================================================

.. code-block:: bash

    licorice generate <model_name>

Generate LiCoRICE user-level per-tick Python snippet files. This includes parsers, constructors, and destructors. Filenames are taken from module definintions in the YAML configuration and files are written to the default module directory (overridden by ``LICORICE_MODULE_PATH``). The generated files are just a scaffold and must be filled out by the user with code that will run for that module function each tick.




Parse
===============================================================================

.. code-block:: bash

    licorice parse <model_name>

Parse a LiCoRICE YAML file. This command reads in and validates the LiCoRICE model, constructs any variables needed for templating, and writes rendered template files to the default output directory (overridden by ``LICORICE_OUTPUT_DIR``)


Compile
===============================================================================

.. code-block:: bash

    licorice compile <model_name>

Compile a LiCoRICE model from the files written to the model output directory. This currently just runs ``make clean`` and ``make`` from the output directory, which compiles all the Cython and C files to executables.


Run
===============================================================================

.. code-block:: bash

    licorice run <model_name>

Runs a LiCoRICE model from the compiled executables in the model output directory. This is as simple as running the timer executable with the right priority which kicks off the rest of the module processes.

Go
===============================================================================

.. code-block:: bash

    licorice go <model_name>

Combine the behavior of ``parse``, ``compile``, and ``run`` into a single command for convenience.

Export
===============================================================================

.. code-block:: bash

    licorice export <model_name>

Export LiCoRICE module and output directories to the export directory (overridden by ``LiCORICE_EXPORT_DIR``)


*******************************************************************************
Reference
*******************************************************************************

The full CLI command reference can be viewed by running ``licorice -h`` and is printed below for convenience:

.. program-output:: licorice -h
