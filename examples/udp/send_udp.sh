#!/bin/bash

# TODO move this to a Python program

PORT=51002          # port number to read from (bind to)
INTERFACE=localhost # interface name

if [[ $OSTYPE == 'darwin'* ]]; then
  NC_OPTIONS=uc
else
  NC_OPTIONS=4u
fi

while :
do
  # netcat options:
  # -4 ipv4 address
  # -u UDP
  # -w timeout (seconds)
  # -N    Shutdown the network socket after EOF on stdin
  echo "STAN" | nc -$NC_OPTIONS -w 1 $INTERFACE $PORT
  echo "FORD" | nc -$NC_OPTIONS -w 1 $INTERFACE $PORT
  echo "TREE" | nc -$NC_OPTIONS -w 1 $INTERFACE $PORT
  echo "MESS" | nc -$NC_OPTIONS -w 1 $INTERFACE $PORT
  echo "AGES" | nc -$NC_OPTIONS -w 1 $INTERFACE $PORT
done
