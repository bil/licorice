#!/bin/bash

port=51002     # port number to read from (bind to)
interface=localhost # interface name

while :
do
  echo "STAN" | nc -4vu -w 1 $interface $port
  echo "FORD" | nc -4vu -w 1 $interface $port
  echo "TREE" | nc -4vu -w 1 $interface $port
  echo "MESS" | nc -4vu -w 1 $interface $port
  echo "AGES" | nc -4vu -w 1 $interface $port
  # echo "SEND" | nc -4vu -w 1 $interface $port
  # echo "TIME" | nc -4vu -w 1 $interface $port
  # echo "FOUR" | nc -4vu -w 1 $interface $port
  # echo "WORD" | nc -4vu -w 1 $interface $port
  # echo "DONE" | nc -4vu -w 1 $interface $port
  #nc = netcat
  #-4 ipv4 addresses
  #v verbose
  #u UDO
  #w timeout for _
done