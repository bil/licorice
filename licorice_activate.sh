# run via: source licorice_activate.sh
# this MUST be run from within the licorice repository directory

REPO_CHECK=1
if [ ! -d "examples" ] || [ ! -d "install" ] || [ ! -d "licorice" ]
then
  echo "This does not look like a LiCoRICE repository!"
  REPO_CHECK=0
fi

if [ $REPO_CHECK -eq 1 ]
then
  LICORICE_ROOT=$( cd "$( dirname "${BASH_SOURCE[0]:-$0}" )" && pwd )
  LICORICE_PS1_STR=LiCoRICE

  EXPERIMENT_DIR=$LICORICE_ROOT/..
  BINARY_DIR=$EXPERIMENT_DIR/run/out


  # export env variables
  export LICORICE_ROOT
  export LICORICE_PS1_STR
  export EXPERIMENT_DIR
  export BINARY_DIR


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
    rm -f /dev/shm/*
  }

  # deactivate licorice environemnt
  licorice_deactivate() {

    PS1=${PS1:(${#LICORICE_PS1_STR}+3)}

    unset LICORICE_ROOT

    unset LICORICE_PS1_STR
    unset EXPERIMENT_DIR
    unset BINARY_DIR

    unset -f licorice_wipe_binaries
    unset -f licorice_shm_clear
    unset -f licorice_deactivate
  }

  export LICORICE_ROOT
  # export shell functions
  if [ -n "${BASH_VERSION}" ]
  then
    export -f licorice_wipe_binaries
    export -f licorice_shm_clear
  fi

  # change prompt
  PS1="[$LICORICE_PS1_STR] $PS1"
  export PS1

fi
