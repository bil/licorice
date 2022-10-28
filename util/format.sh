SRC_DIR="$(dirname "$0")"/..
isort $SRC_DIR
black $SRC_DIR
flake8 $SRC_DIR
