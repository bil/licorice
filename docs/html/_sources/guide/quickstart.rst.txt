*******************************************************************************
LiCoRICE Quickstart
*******************************************************************************

Welcome to LiCoRICE! We're excited to help you bring the principles of realtime computing to your conventional hardware. This guide provides instructions on how to build a simple model from scratch.


0. Prerequisites
===============================================================================

This guide assumes that you're working in a BASH shell on a POSIX-compliant system and have followed the :ref:`LiCoRICE installation instructions <install/licorice:Installation>`.

1. Simple Hello World
===============================================================================

This first hello world example will create a LiCoRICE model that outputs a message once a second 10 times. We'll write everything from scratch.

Create a workspace
-------------------------------------------------------------------------------

In this example, we'll assume you're using ``~/licorice`` as your workspace.

.. code-block:: bash

    export LICORICE_WORKING_PATH=~/licorice
    mkdir $LICORICE_WORKING_PATH

The above sets the ``LICORICE_WORKING_PATH`` :ref:`environment variable <api/env_vars:environment variables>` and creates the directory. This tells LiCoRICE where to look for model and module files. Feel free to change the path to anything that's convenient on your system.


Specify the model
-------------------------------------------------------------------------------

Create the model file:

.. code-block:: bash

    touch $LICORICE_WORKING_PATH/quickstart-1.yaml

Open the created file add the following:

.. code-block:: yaml

    config:
      tick_len: 1000000  # tick length in microseconds (1s)
      num_ticks: 10  # number of ticks to run for
      init_buffer_ticks: 1  # number of ticks that run before time t=0

    modules:
      counter_simple:
        language: python
        constructor: true

This specifies a LiCoRICE model that has a single module, ``counter_simple`` which will run 10 times over 10 seconds and must complete its execution once every 1 second.



Generate modules
-------------------------------------------------------------------------------

.. code-block:: bash

    licorice generate quickstart-1 -y

This should generate two files: ``$LICORICE_WORKING_PATH/counter_simple.py`` and ``$LICORICE_WORKING_PATH/counter_simple_constructor.py``.


Write modules
-------------------------------------------------------------------------------

Open the constructor (``$LICORICE_WORKING_PATH/counter_simple_constructor.py``) and add the following:

.. code-block:: python

    counter = 0

Then open the parser (``$LICORICE_WORKING_PATH/counter_simple.py``) and add the following:

.. code-block:: python

    print(f"Hello World! Tick: {counter}", flush=True)
    counter += 1

The constructor will çreate a variable ``counter`` and set it to ``0`` before realtime execution starts. Then, each tick, the value of ``counter`` will be output and incremented. We interpolate a `Python f-string <https://docs.python.org/3/tutorial/inputoutput.html#formatted-string-literals>`_ with the counter value and flush stdout so that the output appears in our terminal immediately.


Run LiCoRICE
-------------------------------------------------------------------------------

In general, only one command (``go``) needs to be issued to :ref:`parse <api/cli:Parse>`, :ref:`compile <api/cli:Compile>`, and :ref:`run <api/cli:Run>` a model, but these commands can also be issued individually if need be:

.. code-block:: bash

    licorice go quickstart-1 -y

If everything worked, you should see the following among the output in your terminal:

.. code-block:: bash

    Hello World! Tick: 0
    Hello World! Tick: 1
    Hello World! Tick: 2
    Hello World! Tick: 3
    Hello World! Tick: 4
    Hello World! Tick: 5
    Hello World! Tick: 6
    Hello World! Tick: 7
    Hello World! Tick: 8
    Hello World! Tick: 9


2. Pass a Signal
===============================================================================

The first example showed you how to set up a simple LiCoRICE model with one module. Here, we'll split that module in two and use a `signal` to pass data from the first module to the second.

Update model config
-------------------------------------------------------------------------------

Copy over the model config to a different file:

.. code-block:: bash

    cp $LICORICE_WORKING_PATH/quickstart-1.yaml $LICORICE_WORKING_PATH/quickstart-2.yaml

First, add another top-level block called signals with our signal definition as follows:

.. code-block:: yaml

    signals:
      tick_count:
        shape: 1
        dtype: int32

This defines a NumPy array that can be shared between our models.

Now, add another module nested under ``modules:`` with the following info:

.. code-block:: yaml

    modules:
      tick_counter:
        language: python
        constructor: true
        out:
          - tick_count

      ...

The ``tick_counter`` module will have a constructor and is responsible for outputting the ``tick_count`` signal.

Next, change the name of the ``counter_simple`` module to ``counter`` so we can generate a new set of module files and remove its constructor. It also must take ``tick_count`` as an input:

.. code-block:: yaml

    modules:
      ...

      counter:
        language: python
        in:
          - tick_count


This model now defines two modules with a signal passed between them.


Generate modules
-------------------------------------------------------------------------------

Go ahead and generate a new set of module files to use for this model.

.. code-block:: bash

    licorice generate quickstart-2 -y

This should generate three files: two module files and one constructor.


Write modules
-------------------------------------------------------------------------------

Open the ``tick_counter`` constructor (``$LICORICE_WORKING_PATH/tick_counter_constructor.py``) and add the following:

.. code-block:: python

    counter = 0

This is basically doing the job of the constructor from the previous example.

Then open the ``tick_counter`` parser (``$LICORICE_WORKING_PATH/tick_counter.py``) and add the following:

.. code-block:: python

    tick_count[:] = counter
    counter += 1

Instead of printing the ``counter`` variable directly in the module as before, we pass it along as a LiCoRICE signal that can be read by the ``counter`` module.

Finally, open the ``counter`` and add the following line:

.. code-block:: python

    print(f"Hello World! Tick: {tick_count[0]}", flush=True)

The functionality of this model is the same as ``quickstart-1``, but the logic of the ``counter-simple`` module is split between one module that keeps track of the tick number and one that outputs over stdout. A signal passes information between these two processes. This has the advantage of allowing us to create multiple modules that will read from the signal in parallel.


Run LiCoRICE
-------------------------------------------------------------------------------

Run the new model:

.. code-block:: bash

    licorice go quickstart-2 -y

Now you should see the same output as the ``quickstart-1`` model in your terminal.


3. Add Logging
===============================================================================

LiCoRICE also allows you to log signals so that the entire history of a model's run can be examined after the fact.

Update model config
-------------------------------------------------------------------------------

Copy over the model config to a different file:

.. code-block:: bash

    cp $LICORICE_WORKING_PATH/quickstart-2.yaml $LICORICE_WORKING_PATH/quickstart-3.yaml

Open up the ``quickstart-3.yaml`` model file and set the ``log`` flag on the ``tick_count`` signal:

.. code-block:: yaml

    signals:
      tick_count:
        shape: 1
        dtype: int32
        log: true

And then add a logger module (sink) which will be responsible for writing this signal to disk:

.. code-block:: yaml

    modules:

      ...

      logger:
      language: python
      in:
        - tick_count
      out:
        name: log_sqlite
        args:
          type: 'disk'
          save_file: './data'

Run LiCoRICE
-------------------------------------------------------------------------------

Run the new model:

.. code-block:: bash

    licorice go quickstart-3 -y

You should see the same output as the ``quickstart-2`` model in your terminal, but there should also be a SQLite database file that was created in the LiCoRICE output directory.


Examine the results
-------------------------------------------------------------------------------

TODO: Make sure user has installed sqlite3 with ``sudo apt install sqlite3``

To examine the SQLite database file, run:

.. code-block:: bash


    sqlite3 $LICORICE_WORKING_PATH/quickstart-3.lico/out/data_0000.db "select * from signals;"

And you should see the value of the ``tick_count`` variable over time:

.. code-block::

    0
    1
    2
    3
    4
    5
    6
    7
    8
    9



4. Output an External Signal
===============================================================================

So far, we've only dealt with internal modules and signals. These pass data and perform computation within LiCoRICE and aren't meant to interact with external processes or devices. In this model, we'll see how to output a digital signal from LiCoRICE over parallel port that can be read by an oscilloscope.

Prerequisite Hardware
-------------------------------------------------------------------------------

To output and view our parallel port external signal, we'll need some specific hardware:

 * PC with two empty PCIe slots
 * 2x PCIe parallel port adapter. We recommend cards that work automatically with the Linux kernel and don't require a separate driver such as `this one <https://www.amazon.com/dp/B07PXB77W6>`_.
 * 2x `DB25 male-to-female parallel cable  <https://www.amazon.com/Your-Cable-Store-Serial-Female/dp/B0026K9MAG>`_
 * 2x `parallel breakout board <https://www.amazon.com/Connector-D-sub-25-pin-Terminal-Breakout/dp/B073RG3GG6>`_
 * 4x `male-to-male jumper wires <https://www.amazon.com/EDGELEC-Breadboard-Multicolored-1pin-1pin-Connector/dp/B07GD1ZCHQ/>`_
 * oscilloscope. You're welcome to use any oscilloscope that you have on hand, but for our examples, we use the `Hantek DSO2D10 <https://www.amazon.com/Hantek-DSO2C10-Benchtop-Oscilloscope-100MHz/dp/B08YNZTFJS>`_  (`docs <http://hantek.com/products/detail/17182>`_) since it's fairly inexpensive and has a signal generator and persist function which lets us monitor our ``tick_count`` signal over time.


Hardware Setup
-------------------------------------------------------------------------------

If the two parallel port cards are not already installed in your computer, open up your PC's case and plug them in. If you're using the recommended card above with a low-profile expansion slot, you'll have to remove the bracket and serial port and install the included low-profile bracket. After installing the two parallel ports in your PC, you should see that ``ls /dev/parport*`` returns ``/dev/parport0 /dev/parport1``. If this isn't the case, the easiest solution is unfortunately to use different parallel port adapters. If you're unfamiliar with installing PCI-e cards, feel free to watch `this video <https://www.youtube.com/watch?v=p9pTv1S5gsw>`_.

Once your PC is set up correctly, you'll need to connect the male side of each parallel cable to your PC and the female sides to breakout boards. Then, you can loosen the screws on the breakout board to insert jumper wires to the breakout board. For each breakout board, connect one jumper wire to one of the GND pins (pin 25) and one jumper wire to one of the data pins (pin 9). Tighten breakout board screws. `Parallel port pinout for reference <https://en.wikipedia.org/wiki/Parallel_port#/media/File:Parallel_port_pinouts.svg>`_.

Finally, connect your BNC oscilloscope probes with the probe connected to pin 9 on each breakout board and the black alligator clip connected to pin 25 on each breakout board. We'll connect channel 1 to the breakout board connected to our first parallel port (``/dev/parport0``) and channel 2 to ``/dev/parport1``. If you're not sure which is which, connect it either way and change it after viewing the program output.

Permissions
-------------------------------------------------------------------------------

Make sure the user running LiCoRICE can access the port by adding them to the ``lp`` group as follows:

  .. code-block:: bash

    sudo usermod -aG lp <user>

Then log out and back in for the changes to take effect. Note that you'll have to reset environment variables such as ``$LICORICE_WORKING_PATH`` after restarting your session.


Update model config
-------------------------------------------------------------------------------

Copy over the model config to a different file:

.. code-block:: bash

    cp $LICORICE_WORKING_PATH/quickstart-3.yaml $LICORICE_WORKING_PATH/quickstart-4.yaml


Add a parallel port sink that will take in ``tick_count`` and output the result over our connected parallel port:

.. code-block:: yaml

    modules:
      ...

      parallel_writer:
        language: python
        in:
          - parallel_out
        out:
          name: parport_out
          args:
            type: parport
            addr: 1

This creates a sink process which uses the in-built ``parport`` driver outputting over ``/dev/parport1``.

We'll also add a ``parallel_toggle`` module under ``modules`` that will create the signal which controls the parallel port:


.. code-block:: yaml

    modules:
      parallel_toggle:
        language: python
        constructor: true
        out:
          - parallel_out

      ...

We then need to define the ``parallel_out`` signal as follows:

.. code-block:: yaml

    signals:
      ...

      parallel_out:
        shape: 1
        dtype: uint8
        log: true

And add it as an input to the logger:

.. code-block:: yaml

    logger:
      ...
      in:
        - tick_count
        - parallel_out
      ...


Add ``parallel_toggle`` module files
-------------------------------------------------------------------------------

The default behavior of the ``parport`` driver is to take the value of the input signal and write it to the specified parallel port. For that to work, we'll need to set the ``parallel_out`` signal in our ``parallel_toggle`` parser each tick.

Let's generate parser and constructor files for our new module:

.. code-block:: bash

    touch $LICORICE_WORKING_PATH/parallel_toggle.py $LICORICE_WORKING_PATH/parallel_toggle_constructor.py

In the constructor, add the following line:

.. code-block:: python

    toggle_switch = 0b00000000

In the parser add the following lines:

.. code-block:: python

    parallel_out[:] = toggle_switch
    if toggle_switch == 0b00000000:
        toggle_switch = 0b10000000
    else:
        toggle_switch = 0b00000000

The ``0b`` syntax allows us to set each bit individually in the unsigned 8 bit integer signal ``parallel_out``. Here we set only the first bit high (data pin 9), but we could just as easily set all the bits high with ``0b11111111``


Run LiCoRICE
-------------------------------------------------------------------------------

Turn on your oscilloscope and run:

.. code-block:: bash

    licorice go quickstart-4 -y

You should see the same output in the terminal as the ``quickstart-3`` model and a SQLite database in the model output directory, but now you should also see that the green trace (channel 2) on the oscilloscope screen jumps up and down each second. If the output is over channel 1, feel free to switch the BNC probes so that the output signal is on channel 2.


View the oscilloscope output as a square wave
-------------------------------------------------------------------------------

Since the LiCoRICE model only runs for 10 ticks over 10 seconds, we don't have a lot of time to modify the settings on the oscilloscope to see what's going on. Start by commenting out the ``num_ticks`` argument in ``quickstart-4.yaml`` so that the model runs indefinitely and decrease the tick length so we have a 10Hz square wave:

.. code-block:: yaml

    config:
      tick_len: 50000 # tick length in microseconds (50ms)
      #num_ticks: 10  # number of ticks to run for
      ...



Run the model again and while it's running, adjust the oscilloscope to view the square wave output. Start by turning off channel 1 using the ``CH1 MENU`` button and adjust the horizontal scaling using the ``SEC/DIV`` knob until the division legnth shows as 50ms in the topbar. Adjust the vertical position and scale for channel 2 until you see the full signal. A 1V division should be sufficient. If you'd like to stop running the model, you can do so by typing Control-C in the terminal.

Setting a trigger
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Using the ``TRIG MENU`` button, make sure that an `Edge` Type trigger is set on the `CH2` Source and that Slope is set to `Rising`. Then, use the trigger ``LEVEL`` knob to set the trigger to the midpoint of the signal. You should now see something like this:

.. image:: /_images/quickstart_4_1.jpg
  :alt: 10Hz square wave

5. Drive Output from an External Input
===============================================================================

In the last example, we generated a 10Hz square wave in LiCoRICE and output it over an external channel. Here, we will use an external parallel port input to drive our ``parallel_out`` variable which will be output over a second parallel port cable.


Update model config
-------------------------------------------------------------------------------

Copy over the model config to a different file:

.. code-block:: bash

    cp $LICORICE_WORKING_PATH/quickstart-4.yaml $LICORICE_WORKING_PATH/quickstart-5.yaml

Add a source that will read our parallel port input:

.. code-block:: yaml

    modules:
      parallel_reader:
        language: python
        in:
          name: parport_in
          args:
            type: parport
            addr: 0
          schema:
            data:
              dtype: uint8
              size: 1
            max_packets_per_tick: 1
        out:
          - parallel_in

      ...

Similarly to the ``parport`` sink driver, the default ``parport`` source driver behavior is to populate the ``parallel_in`` variable with the data read over parallel port in each tick.

We'll also change the ``parallel_toggle`` module definition to take ``parallel_in`` as an input signal and not use the constructor. Rename the module to ``parallel_through`` so we can use a different module file:

.. code-block:: yaml

    modules:
      ...

      parallel_through
        ...
        constructor: false
        in:
          - parallel_in
        ...

      ...

Lastly, add the ``parallel_in`` signal which will have a similar definition as the ``parallel_out``, just without logging.

.. code-block:: yaml

    parallel_in:
      shape: 1
      dtype: uint8

Update toggler module
-------------------------------------------------------------------------------

Open a new file named ``$LICORICE_WORKING_DIR/parallel_through.py`` and update it with the following:

.. code-block::

    parallel_out[:] = parallel_in


Set up the oscilloscope function generator
-------------------------------------------------------------------------------

First, we'll need to ouput a signal over our oscilloscope that will drive LiCoRICE. Use a 10Hz square wave:

Connect a BNC to Jaw clip line cable to the ``EXT TRIG/GEN OUT`` port on the oscilloscopel. Connect the black alligator clip to ground on the ``/dev/parport0`` breakout board and the red alligator clip to pin 9. There should be enough room on the jumper cable terminals to connect the channel 1 probe as well. Press the ``WAVE GEN`` button on the scope to turn on the waveform generator and set Wave: `Square`, Frequency: `10.000Hz`, Amplitude: `3.300V`, and Offset: `0.000V`. You should see the oscilloscope-generated signal on channel 1.


Run LiCoRICE
-------------------------------------------------------------------------------

Run the model:

.. code-block:: bash

    licorice go quickstart-5 -y

You should see all the same outputs as in the previous examples, but now there should be two similar traces on the oscilloscope. Since the oscilloscope and LiCoRICE are both operating on the same clock, the two signals will not necessarily be in phase with each other. To see better phase alignment, try setting the LiCoRICE ``tick_len`` to a lower number, say 10000 (10ms ticks) or 1000 (1ms ticks). Note that operating at such a fast clock rate without a realtime kernel patch (1ms) may cause a timing violation.

..
    TODO add link to kernel patch instructions

Oscilloscope view
-------------------------------------------------------------------------------

To visually see the latency introduced by LiCoRICE on the oscilloscope, change the trigger Source to `CH1` and make sure the ``LEVEL`` knob is set correctly. You should see something like this:

.. image:: /_images/quickstart_5_1.jpg
  :alt: 10Hz square wave being tracked by LiCoRICE output


Manipulate the signal
-------------------------------------------------------------------------------

We've taken the input signal and replicated it at the output, but what if we want to modify it? We can change the ``parallel_through`` module to the following:

.. code-block::

    parallel_out[:] = ~parallel_in


This uses the bitwise NOT operator ``~`` to flip the bits in the ``parallel_in`` signal. After doing this, you should see the ``paralell_out`` signal inverted on the oscilloscope:

.. image:: /_images/quickstart_5_2.jpg
  :alt: 10Hz square wave and inverted LiCoRICE output

..
    TODO maybe add image with lower latency

Conclusion
-------------------------------------------------------------------------------

If you've gotten this far, congrats! You've finished the LiCoRICE quickstart and have learned how to input a signal into a realtime system, manipulate it, log it, and output it back. To learn more about LiCoRICE and work through the rest of the examples, check out the :ref:`full tutorial <guide/tutorial:LiCoRICE Tutorial>`.

