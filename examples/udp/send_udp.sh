#!/bin/bash

# TODO move this to a Python program

PORT=51002          # port number to read from (bind to)
INTERFACE=localhost # interface name

while :
do
  # netcat options:
  # -4 ipv4 address
  # -u UDP
  # -w timeout (seconds)
  # -N    Shutdown the network socket after EOF on stdin
  echo "STAN" | nc -4u -w 1  $INTERFACE $PORT
  echo "FORD" | nc -4u -w 1  $INTERFACE $PORT
  echo "TREE" | nc -4u -w 1  $INTERFACE $PORT
  echo "MESS" | nc -4u -w 1  $INTERFACE $PORT
  echo "AGES" | nc -4u -w 1  $INTERFACE $PORT
done
