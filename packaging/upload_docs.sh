#!/bin/bash

"$(dirname "$0")"/compile_docs.sh
scp -r docs/html/. licorice@docs.licorice.su.domains:/home/licorice/docs/html/
