#!/bin/bash

for i in {1..54} ; do sudo bash -c "echo 1 > /proc/irq/$i/smp_affinity"; done  
