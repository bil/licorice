###############################################################################
Drivers
###############################################################################

LiCoRICE uses the concept of drivers to interface with external systems. LiCoRICE includes drivers for a number of default inputs and outputs and gives users the ability to write custom drivers for additional I/O support. Code for default drivers can be found under the ``licorice/templates/source_drivers`` and
``licorice/templates/sink_drivers`` directories.

*******************************************************************************
Sync vs Async
*******************************************************************************

By default, LiCoRICE input and output driver code is run synchronously inside the respective source or sink. Drivers may also be run asynchronously by specifying the ``async: True`` flag on that driver's external signal. This creates two processes for the asynchronous sources or sink: one *async reader* or *async writer* which reads in or writes data and handles buffering; and another *realtime stamper* which defines tick boundaries in the data by updating buffer housekeeping variables according to the realtime clock.

*******************************************************************************
Custom Drivers
*******************************************************************************

Users may extend LiCoRICE by writing their own drivers to interface with peripherals. For now, sink drivers must be added to the ``licorice/templates/sink_drivers/`` folder and source to ``licorice/templates/source _drivers/``. Eventually, users will be able to add their drivers to custom folders by setting an environment variable.

*******************************************************************************
Example
*******************************************************************************

The following is an implementation of a parallel port source driver which uses pyparallel to read in data each tick. It implements four driver code sections (``imports``, ``variables``, ``setup``, and ``read``) and omits one (``exit_handler``) that is not used. The driver code sections are directly dropped into the source template using `Jinja2 templating <https://jinja.palletsprojects.com/en/3.1.x/>`_. Note that templating can also be used in the driver itself. In this instance, the ``async`` flag is used to ensure that for async modules, the read call happens at most twice per tick (since the ``sleep_duration`` is half a tick-length). The exact same driver can then be used for a synchronous parallel port source since the sleep call will be skipped and reads will happen once per tick.

.. code-block:: cython
  :linenos:

  # __DRIVER_CODE__ imports
  import parallel

  # __DRIVER_CODE__ variables

  cdef unsigned char inVal


  # __DRIVER_CODE__ setup

  pport = parallel.Parallel(port={{in_signal['args']['addr']}})
  pport.setDataDir(False) # read from data pins, sets PPDATADIR
  sleep_duration = {{config["config"]["tick_len"]}} / (2. * 1e6)

  # __DRIVER_CODE__ read

    inVal = <unsigned char>pport.getData()
    bufCurPtr[0] = inVal

  {%- if async %}

    sleep(sleep_duration)
  {%- endif %}
