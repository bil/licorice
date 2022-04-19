#!/bin/bash

# Usage: Make sure setup.py is updated with the latest version number and
# run this script from the default branch.

GIT_CURRENT_BRANCH=`git branch --show-current`
GIT_DEFAULT_BRANCH=`git remote show origin | sed -n '/HEAD branch/s/.*: //p'`
GIT_VERSION_TAG="v$(python setup.py --version)"

if [ $GIT_CURRENT_BRANCH != $GIT_DEFAULT_BRANCH ]; then
    echo "No action taken. Switch to default branch."
    exit 1
fi

if [ git rev-parse $GIT_VERSION_TAG >/dev/null 2>&1 ]; then
    echo "No action taken. Tag exists."
    exit 1
fi

git tag $GIT_VERSION_TAG
git push origin $GIT_VERSION_TAG
