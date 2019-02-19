#!/bin/bash
# Shell script that handles allowing a single serial port to function as both a sink and a source
#
# this runs as user, so ensure that the user has serial port permissions
#    in Debian/Ubuntu, this involves becoming a member of the dialout group

SERIAL_PORT=/dev/ttyS0

if [ -e /tmp/fifo_source ]
then
  rm /tmp/fifo_source
fi
if [ -e /tmp/fifo_sink ]
then
  rm /tmp/fifo_sink
fi
mkfifo /tmp/fifo_source
mkfifo /tmp/fifo_sink

socat -u /tmp/fifo_sink - | socat - $SERIAL_PORT,b115200,cr,ignbrk=1 | socat -u - /tmp/fifo_source
