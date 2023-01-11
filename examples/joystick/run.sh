CWD="$(dirname "$0")"
LICORICE_WORKING_PATH=$CWD LICORICE_MODULE_PATH="$CWD:$(dirname "$CWD")/pygame_shared" licorice go joystick_demo -y "$@"
