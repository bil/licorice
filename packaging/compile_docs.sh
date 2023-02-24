#!/bin/bash

make clean
make -C docs html
rm -rf ./docs/html
cp -r docs/build/html/. ./docs/html

