*******************************************************************************
YAML Configuration Reference
*******************************************************************************

LiCoRICE uses YAML configuration files to specify the model that will be constructed and run.


Models
===============================================================================

Models define the architecture of your realtime analysis pipeline from data
acquisition (sources) to processing (modules) to output (sinks). Models are
defined through `yaml <https://www.cloudbees.com/blog/yaml-tutorial-everything-you-need-get-started>`_
files and are broken up into the following sections:

* :ref:`api/yaml_config:config`
* :ref:`api/yaml_config:signals`
* :ref:`api/yaml_config:modules`


Config
-------------------------------------------------------------------------------

High-level configuration variables are set by the user here. Here we define aspects of the setup, timing, and ticks(our metric of time) in order to control the way our system interacts with the real world.

================= =============================================================
Keyword           Description
================= =============================================================
tick_len          Realtime clock frequency in microseconds
num_ticks         Number of ticks to run the model for. Defaults to -1
                  (indefinite)
sys_mask          CPU bitmask indicating which cores are available for
                  system processes to run on. Defaults to CPU0 (e.g., 0x1) in
                  realtime mode and all cores (e.g., 0xff for 8 cores) or no
                  action in non-realtime mode.
lico_mask         CPU bitmask indicating which cores are available for
                  LiCoRICE to run on. Defaults to all cores besides the system
                  core in realtime mode (e.g., 0xfe for 8 cores) and all cores
                  in non-realtime mode.
source_init_ticks Number of ticks to run sources before modules start
module_init_ticks Number of ticks to run sources and modules before
                  sinks start
================= =============================================================


Signals
-------------------------------------------------------------------------------

Here we define how data will be passed between our modules. We also define how much of this data to keep over time and how to store it if necessary for our use case. At a high-level, signals are represented as NumPy arrays in our modules. However, in implementation, they are actually shared arrays, shared memory that allows for the fast transfer of data between models required for realtime analysis.


============= ===============================================================
Keyword       Description
============= ===============================================================
shape         The shape of the numpy signal as a tuple (single tick)
dtype         The dtype of the numpy signal
history       Number of ticks of data to store in memory
latency       Fixed latency to introduce to ndarray indexing.
log           bool specifying whether or not to log the signal or dict
              specifying log arguments
============= ===============================================================


Modules
-------------------------------------------------------------------------------

Modules are the primary building blocks of LiCoRICE. Here we define the name of our module, the language it's in (Python or C), what signals, if any, will be streaming in, and what signals, if any, will be streaming out. We also define whether this module will use a parser to read or write external signals, a constructor to prepare data or initialize processes, or a destructor to stop processes or clean data.

LiCoRICE will automatically detect whether a module is a source, sink, or
internal module given the signals attributed to that module.

============ ==================================================================
Keyword      Description
============ ==================================================================
language     The programming language used to write the module (Python or C)
constructor  Indicates that a constructor is used to initialize the module
parser       Indicates that a parser is used for tick-level code (only for
             sources and sinks)
destructor   Indicates that a destructor is used to teardown resources
in           Defines module and sink inputs as an array. Defines source input
             as a dict
out          Defines module and source outputs as an array. Defines sink output
             as a dict
============ ==================================================================

.. TODO

    expand. include detailed information about filename conventions

External Signals
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

External signals are information that is passed in and out of our model. Having an external signal is what defines modules as either a sink or a source(any module should only ever have one). Given the inherent complexity of dealing with external devices or applications, additional information is needed to define these signals.

..
    TODO

    * in-built source drivers
    * in-built sink drivers

Example Model
===============================================================================

.. code-block:: yaml
    :linenos:

    config:

      tick_len: 100000 # in microseconds (0.1s)
      # number of ticks to run for; defaults to -1 (run until terminated by the user)
      num_ticks: 10


    signals:

      signal_1:
        shape: (2, 2) # All signals are be treated as numpy arrays
        dtype: float64
        history: 1 # How much previous data to keep on the signal in the system

       signal_2:
        shape: 1 # Signals can also be 1D
        dtype: float64


    modules:

      sum_init:
          language: python  # can be C or python
          constructor: True. # signifies we will use a constructor
          in:   # An External Signal (Joystick in USB)
            name: joystick_raw
            args:
                type: pygame_joystick
            schema:
                max_packets_per_tick: 1 # defaults to 1 for sync, None for async
                data:
                    dtype: double
                    size: 2
          out:
            - signal_1

        sum:
            language: python
            in:
                - signal_1
            out:
                - signal_2

        sum_print:
            language: python
            in:
              - signal_2
