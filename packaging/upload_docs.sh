#!/bin/bash

"$(dirname "$0")"/compile_docs.sh
rsync -a --delete docs/html/ licorice@docs.licorice.su.domains:/home/licorice/docs/html/
