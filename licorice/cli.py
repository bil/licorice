import argparse
import os
import shlex
import subprocess
from distutils.sysconfig import get_python_lib
from functools import lru_cache
from warnings import warn

import yaml

import licorice.template_funcs as template_funcs
from licorice.utils import __handle_completed_process


def __load_and_validate_model(file):
    filepath = None
    model_abspath = os.path.abspath(os.environ.get("LICORICE_MODEL_DIR") or "")
    working_abspath = os.environ.get("LICORICE_WORKING_DIR")
    if not working_abspath:
        working_abspath = ""
    else:
        working_abspath = os.path.join(
            os.path.abspath(working_abspath), "models"
        )

    # add working dir and/or extension to config filepath if necessary
    for ext in ["", ".yaml", ".yml"]:
        for pre in set(["", model_abspath, working_abspath]):
            if os.path.exists(os.path.join(pre, file + ext)):
                filepath = os.path.join(pre, file + ext)
                break

    if not filepath:
        raise ValueError(
            f"Could not locate model file: {file}. Specify a full path or set LICORICE_WORKING_DIR and/or other env vars."
        )

    # load model
    with open(filepath, "r") as f:
        try:
            model = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            print(exc)

    # this assumes that a top level object with three primary mappings is loaded
    # the only three mappings should be: config, signals, and modules
    # later versions should throw an error if this is not true
    # Relevant note: this entire parser is dangerous and does not have any safety checks
    #    it will break badly for malformed yaml data
    top_level = ["config", "modules", "signals"]
    if not set(model.keys()).issubset(set(top_level)):
        raise RuntimeError("Invalid model definition.")

    return model


def __get_licorice_paths():
    paths = {}

    # set some paths
    paths = {}

    # TODO allow this to accept a list of paths so users can add templates
    dir_path = os.path.dirname(os.path.realpath(__file__))
    paths["templates"] = os.path.join(dir_path, "templates")
    paths["generator"] = os.path.join(dir_path, "generators")

    licorice_working_dir = os.environ.get("LICORICE_WORKING_DIR")
    if not licorice_working_dir:
        licorice_working_dir = os.getcwd()
        warn(
            "LICORICE_WORKING_DIR env var not set. Using pwd as working directory.",
            RuntimeWarning,
        )

    paths["modules"] = os.environ.get("LICORICE_MODULE_DIR") or os.path.join(
        licorice_working_dir, "modules"
    )
    paths["output"] = os.environ.get("LICORICE_OUTPUT_DIR") or os.path.join(
        licorice_working_dir, "run/out"
    )
    paths["export"] = os.environ.get("LICORICE_EXPORT_DIR") or os.path.join(
        licorice_working_dir, "run/export"
    )

    paths["tmp_modules"] = os.environ.get(
        "LICORICE_TMP_MODULE_DIR"
    ) or os.path.join(licorice_working_dir, ".modules")
    paths["tmp_output"] = os.environ.get(
        "LICORICE_TMP_OUTPUT_DIR"
    ) or os.path.join(licorice_working_dir, "run/.out")

    return paths


def __execute_iterable_output(cmd, **kwargs):
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        shell=True,
        bufsize=1,
        **kwargs,
    )
    for stdout_line in iter(process.stdout.readline, ""):
        yield stdout_line
    process.stdout.close()
    return_code = process.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)


def export_model(confirm=False):
    paths = __get_licorice_paths()
    template_funcs.export(paths, confirm)


def generate_model(model_file, confirm=False):
    model = __load_and_validate_model(model_file)
    paths = __get_licorice_paths()
    template_funcs.generate(paths, model, confirm)


def parse_model(args):
    args = __parse_args()
    model = __load_and_validate_model(args.model)
    paths = __get_licorice_paths()
    template_funcs.parse(paths, model, args.confirm)


def compile_model(args):
    paths = __get_licorice_paths()

    # make clean
    __handle_completed_process(
        subprocess.run(
            ["make", "clean"], cwd=paths["output"], capture_output=True
        ),
        print_stdout=True,
    )

    # make
    __handle_completed_process(
        subprocess.run(
            ["make", "-j", f"{os.cpu_count()}"],
            cwd=paths["output"],
            capture_output=True,
        ),
        print_stdout=True,
    )


def run_model(args):
    paths = __get_licorice_paths()
    os_env = os.environ.copy()
    os_env["PYTHONPATH"] = get_python_lib()
    if args.rt:
        # TODO look at taskset 0x1 and if sudo is needed
        run_cmd = "nice -n -20 ./timer"
    else:
        run_cmd = "./timer"
    for line in __execute_iterable_output(
        shlex.split(run_cmd),
        cwd=paths["output"],
        env=os_env,
    ):
        print(line, end="", flush=True)


def go(args):
    parse_model(args)
    compile_model(args)
    run_model(args)


command_dict = {
    "go": go,
    "parse": parse_model,
    "compile": compile_model,
    "run": run_model,
    "generate": generate_model,
    "export": export_model,
}


@lru_cache(maxsize=None)
def __parse_args():
    print("Executing parse_args")
    # do some argument parsing
    arg_parser = argparse.ArgumentParser(description="LiCoRICE config parser.")
    arg_parser.add_argument(
        "cmd",
        type=str,
        help="LiCoRICE command to run.",
        choices=command_dict.keys(),
    )
    arg_parser.add_argument("model", type=str, help="YAML model file to parse")
    arg_parser.add_argument(
        "-y",
        "--confirm",
        action="store_true",
        help="ask for user confirmation on action",
    )
    arg_parser.add_argument(
        "--rt",
        "--realtime",
        action="store_true",
        help="run LiCoRICE with realtime timing guarantees",
    )
    args = arg_parser.parse_args()

    return args


def main():
    args = __parse_args()

    command_dict[args.cmd](args)


if __name__ == "__main__":
    main()
