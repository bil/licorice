*******************************************************************************
Drivers
*******************************************************************************

LiCoRICE uses the concept of drivers to interface with external systems. LiCoRICE includes drivers for a number of default inputs and outputs and gives users the ability to write custom drivers for additional I/O support. Code for default drivers can be found under the ``licorice/templates/source_drivers`` and
``licorice/templates/sink_drivers`` directories.


Sync vs Async
===============================================================================

By default, LiCoRICE input and output driver code is run synchronously inside the respective source or sink. Drivers may also be run asynchronously by specifying the ``async: True`` flag on that driver's external signal. This creates two processes for the asynchronous sources or sink: one *async reader* or *async writer* which reads in or writes data and handles buffering; and another *realtime stamper* which defines tick boundaries in the data by updating buffer housekeeping variables according to the realtime clock.


In-built Drivers
===============================================================================

Source Drivers
-------------------------------------------------------------------------------

line
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Coming soon.

parport
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Coming soon.

pipe
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Coming soon.

pygame_joystick
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Coming soon.

udp
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Coming soon.

zmq
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Coming soon.

Sink Drivers
-------------------------------------------------------------------------------


disk
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The disk sink driver defines a specialized logger output that creates SQLite database files for use  in recording data from systems neuroscience experiments. Disk sinks should be defined as asynchronous since I/O operations will generally not fall within the realtime tick boundaries.

The disk driver's behavior is defined in the YAML model file by an ``args`` dict on the sink output signal as well as a ``log`` dict on the signal definitions of the input signal. It creates a ``tick`` table by default which logs one row per LiCoRICE tick and includes 4 timing signals for which definitions are found in :ref:`Modules Properties <basic/modules:common properties>`.

An example of the disk sink output signal ``args`` is as follows:

.. code-block:: yaml

    out:
        name: sqlite_log_out_signal
        async: True
        args:
            type: disk
            tick_table: tick
            save_file: ./data


And this ``args`` dict has the full specification:

=================== ========= =================================================
Name                Type      Description
=================== ========= =================================================
type                string    Must be set to ``disk``
tick_table          string    Table name for tick-level table. This name must
                              be valid in SQLite since it is spliced into SQL
                              command without any error checking
save_file           string    Name of file for where data for the experiment
                              should be stored. 48 character limit. DO NOT add
                              .db to the end

=================== ========= =================================================

Disk driver sinks may also take input signals that run at different frequencies to the LiCoRICE model and therefore would be cumbersome to store in the tick-level table. By specifying a ``log`` dict on the signal definition and setting the ``table`` keyword, signals can be logged in their own table with one row per timestep. If multiple non-tick signals are stored in the same table, they must be time-locked.

An example of the signal-level ``log`` dict is as follows:

.. code-block:: yaml

    log:
        enable: True
        table: two_khz
        save_file: ./data

This ``log`` dict may be simply a boolean to use disk defaults or can specify the arguments in a dict with the following keys:

=================== ========= =================================================
Name                Type      Description
=================== ========= =================================================
enable              boolean   Whether or not this signal should be logged. Defaults to True
type                string    ``scalar``, ``vector``, ``msgpack``, or ``text``.
                              Defaults to ``auto`` which will pick the best among the first three options given signal shape and dtype.
table               string    The name of the table for this signal to be
                              logged in. If this value is the same across
                              multiple signals, then those signals **must** be
                              time-locked meaning they produce the same amount
                              of data on the same ticks
=================== ========= =================================================

**NOTE:** Although all the keys are optional, at least one key must be specified in the dict so that the YAML syntax is valid

Using multiple disk sinks at once has not been tested.



line
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Coming soon.

parport
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Coming soon.

pipe
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Coming soon.


udp
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Coming soon.

vis_pygame
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Coming soon.

zmq
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Coming soon.

