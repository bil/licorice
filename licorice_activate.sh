# run via: source licorice_activate.sh
# this MUST be run from within the licorice repository directory

LICORICE_DIR=`pwd`
LICORICE_TEMPLATING_DIR=$LICORICE_DIR/templating
LICORICE_EXEC_STR="sudo PYTHONPATH=$VIRTUAL_ENV/lib/python2.7/site-packages taskset 0x1 nice -n -20 ./timer"
LICORICE_PS1_STR=LiCoRICE

# small sanity check to ensure in the correct directory
if [ ! -f "LICENSE" ] && [ ! -f "README.md" ]
then
  echo "Not in LiCoRICE repository directory! Run from LiCoRICE repository root."
  return
fi

# parse LiCoRICE model
licorice_parse_model() {
  cd $LICORICE_TEMPLATING_DIR
  python lico_parse.py -c $LICORICE_DIR/../config.yaml -m $LICORICE_DIR/../models/$1.yaml
}

# compile LiCoRICE model
licorice_compile_model() {
  cd $LICORICE_DIR/../run/out
  make clean
  make -j 2
}

# run LiCoRICE model
licorice_run_model() {
  licorice_shm_clear
  $LICORICE_EXEC_STR
}

# remove any compiled binaries
licorice_wipe_binaries() {
  rm -rf $LICORICE_DIR/../run/out/*
}

# remove shm mappings
licorice_shm_clear() {
  sudo rm -rf /dev/shm/*
}

# parse, compile, & run LiCoRICE model
licorice_go() {
  licorice_wipe_binaries
  licorice_parse_model $1
  licorice_compile_model
  licorice_run_model
}

# deactivate licorice environemnt
licorice_deactivate() {
  unset -f licorice_parse_model
  unset -f licorice_compile_model
  unset -f licorice_run_model
  unset -f licorice_wipe_binaries
  unset -f licorice_shm_clear
  unset -f licorice_go
  unset -f licorice_deactivate
  PS1=${PS1:(${#LICORICE_PS1_STR}+3)}
}

# export shell functions
export -f licorice_parse_model
export -f licorice_compile_model
export -f licorice_run_model
export -f licorice_wipe_binaries
export -f licorice_shm_clear
export -f licorice_go

# change prompt
PS1="[$LICORICE_PS1_STR] $PS1"
export PS1
