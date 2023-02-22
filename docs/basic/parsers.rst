*******************************************************************************
Parsers
*******************************************************************************

LiCoRICE uses parsers to convert external buffers to internal signals and vice versa. This allows a 1-dimensional buffer passed into LiCoRICE through a driver to be treated as multiple n-dimensional signals. Or it can define how multiple signals are packed into a buffer for output. Parsers also allow the user to define a packet structure for their data which differs from the default. If no parser is specified, LiCoRICE expects there to be only one signal and for the buffer size and type to match that of the signal.

In general, parsers can be thought of as the tick-level code that runs for a source or sink, similar to the "user code" section of a module. LiCoRICE also provides the ability to add a constructor and a destructor to spin up and tear down resources needed to run the parser.

Source Parsers
===============================================================================

In sources, the parser functions to convert the buffer supplied by the driver (``inBuf``) to a number of signals that can be used by LiCoRICE.

Consider the ``joystick_reader`` source taken from the ``joystick`` demo and defined below:

.. code:: yaml

  ...

  joystick_reader:
    language: python
    parser: True
    in:
      name: joystick_raw
      args:
        type: pygame_joystick
      schema:
        data:
          dtype: uint8
          size: 22
      async: True
    out:
      - joystick_axis
      - joystick_buttons

    ...

This source takes as input the external signal named ``joystick_raw`` which is a 22 element ``uint8`` buffer supplied by the ``pygame_joystick`` driver. It has a parser, which is shown below:

.. code:: cython

    joystick_axis[:] = [ (<double *>inBuf)[0], (<double *>inBuf)[1] ]
    joystick_buttons[:] = [
        (<uint8_t *>inBuf)[128 + i] for i in range(joystick_buttons.size)
    ]

The format of ``inBuf`` is a mixed-type buffer with ``double``\s representing the analog stick x- and y-coordinates followed by an array of enough ``uint8_t``\s to represent the joystick buttons. The parser first casts each of the analog stick coordinates from ``inBuf`` to ``double`` and packs them into the ``joystick_axis`` signal. It then casts each of the button values from ``inBuf`` to ``uint8_t`` and packs them into ``joystick_buttons``. This way, the ``joystick_reader`` source can output a more readable data format than a flat buffer.


Sink Parsers
===============================================================================

Sink parsers do more or less the opposite of source parsers, converting a number of LiCoRICE signals to a buffer that will be supplied to a driver for external output.

..
    TODO add sink parser example
