*******************************************************************************
Drivers
*******************************************************************************

LiCoRICE uses the concept of drivers to interface with external systems. LiCoRICE includes drivers for a number of default inputs and outputs and gives users the ability to write custom drivers for additional I/O support. Code for default drivers can be found under the ``licorice/templates/source_drivers`` and
``licorice/templates/sink_drivers`` directories.


Sync vs Async
===============================================================================

By default, LiCoRICE input and output driver code is run synchronously inside the respective source or sink. Drivers may also be run asynchronously by specifying the ``async: True`` flag on that driver's external signal. This creates two processes for the asynchronous sources or sink: one *async reader* or *async writer* which reads in or writes data and handles buffering; and another *realtime stamper* which defines tick boundaries in the data by updating buffer housekeeping variables according to the realtime clock.
