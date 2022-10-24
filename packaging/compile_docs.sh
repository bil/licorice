#!/bin/bash

if [[ $(git diff --stat) != '' ]]; then
  echo "Dirty working tree. Compiling docs and copying to docs/html/"
  make -C docs html
  cp -r docs/build/html/. docs/html
else
  if git diff --cached --name-only | grep --quiet "^docs/"
  then
    echo "Clean working tree. Compiling docs and copying to docs/html/"
    make -C docs html
    cp -r docs/build/html/. docs/html
    git add docs/html
    echo "Docs built and files staged. Try committing again."
  else
    echo "Skipping build. No changes in docs/"
  fi

fi

