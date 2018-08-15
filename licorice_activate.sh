# run via: source licorice_activate.sh
# this MUST be run from within the licorice repository directory

REPO_CHECK=1
if [ ! -d "examples" ] || [ ! -d "install" ] || [ ! -d "templating" ]
then
  echo "This does not look like a LiCoRICE repository!"
  REPO_CHECK=0
fi

if [ $REPO_CHECK -eq 1 ]
then

  LICORICE_ROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
  LICORICE_TEMPLATING_DIR=$LICORICE_ROOT/templating
  LICORICE_EXEC_STR="sudo PYTHONHOME=$VIRTUAL_ENV taskset 0x1 nice -n -20 ./timer"
  LICORICE_PS1_STR=LiCoRICE
  
  EXPERIMENT_DIR=$LICORICE_ROOT/..
  MODEL_DIR=$EXPERIMENT_DIR/models
  BINARY_DIR=$EXPERIMENT_DIR/run/out
  
  FILE_MODEL_NAME=$BINARY_DIR/model_name
  
  # export env variables
  export LICORICE_ROOT
  export LICORICE_TEMPLATING_DIR
  export LICORICE_EXEC_STR
  export LICORICE_PS1_STR
  export EXPERIMENT_DIR
  export MODEL_DIR
  export BINARY_DIR
  export FILE_MODEL_NAME
  
  
  # parse LiCoRICE model
  licorice_parse_model() {
    pushd $LICORICE_TEMPLATING_DIR
    python lico_parse.py -m $MODEL_DIR/$1.yaml
    popd
  
    printf "%s" "$1" > $FILE_MODEL_NAME
  }
  
  # compile LiCoRICE model
  licorice_compile_model() {
    printf 'Compiling: %s\n\n' "`cat $FILE_MODEL_NAME`"
  
    pushd $BINARY_DIR
    make clean
    make -j 2
    popd
  }
  
  # run LiCoRICE model
  licorice_run_model() {
    printf 'Running: %s\n\n' "`cat $FILE_MODEL_NAME`"
  
    pushd $BINARY_DIR
    licorice_shm_clear
    $LICORICE_EXEC_STR
    popd
  }
  
  # remove any compiled binaries
  licorice_wipe_binaries() {
    if [ -n "$BINARY_DIR" ]
    then
      rm -rf $BINARY_DIR/*
    else
      echo "WARNING: Could not find binaries directory. Not wiping anything."
    fi
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

    PS1=${PS1:(${#LICORICE_PS1_STR}+3)}

    unset LICORICE_ROOT
    unset LICORICE_TEMPLATING_DIR
    unset LICORICE_EXEC_STR
    unset LICORICE_PS1_STR
    unset EXPERIMENT_DIR
    unset MODEL_DIR
    unset BINARY_DIR
    unset FILE_MODEL_NAME
  
    unset -f licorice_parse_model
    unset -f licorice_compile_model
    unset -f licorice_run_model
    unset -f licorice_wipe_binaries
    unset -f licorice_shm_clear
    unset -f licorice_go
    unset -f licorice_deactivate
  }
  
  export LICORICE_ROOT
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

fi
