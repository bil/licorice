#!/bin/bash

# TODO move this to a Python program

PORT=51002          # port number to read from (bind to)
INTERFACE=localhost # interface name

if [[ $OSTYPE == 'darwin'* ]]; then
  NC_OPTIONS=uc
else
  NC_OPTIONS=4u
fi

messages=("STAN" "FORD" "TREE" "MESS" "AGES")

while :
do
  for message in "${messages[@]}"; do
    # netcat options:
    # -4 ipv4 address
    # -u UDP
    # -w timeout (seconds)
    # -N    Shutdown the network socket after EOF on stdin
    echo $message
    echo $message | nc -$NC_OPTIONS -w 1 $INTERFACE $PORT
    case $OSTYPE in
      darwin*)
        sleep 1
        ;;
    esac
  done
done
