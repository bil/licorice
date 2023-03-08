#!/bin/bash

make clean
rm -rf ./docs/html ./docs/build
make -C docs html
cp -r docs/build/html/. ./docs/html

