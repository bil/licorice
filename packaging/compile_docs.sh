#!/bin/bash

make -C docs html
cp -r docs/build/html/. docs/html

