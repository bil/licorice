import argparse
import base64
import hashlib
import json
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
    # TODO split into list of paths
    model_abspath = os.path.abspath(os.environ.get("LICORICE_MODEL_PATH") or "")
    working_abspath = os.environ.get("LICORICE_WORKING_PATH")
    if not working_abspath:
        working_abspath = ""
    else:
        working_abspath = os.path.abspath(working_abspath)

    # add working dir and/or extension to config filepath if necessary
    for ext in ["", ".yaml", ".yml"]:
        for pre in set(["", model_abspath, working_abspath]):
            if os.path.exists(os.path.join(pre, file + ext)):
                filepath = os.path.join(pre, file + ext)
                break

    if not filepath:
        raise ValueError(
            f"Could not locate model file: {file}. Specify a full path "
            " or set LICORICE_WORKING_PATH and/or other env vars."
        )

    # load model
    with open(filepath, "r") as f:
        try:
            model_dict = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            print(exc)

    # This assumes that a top level object with three primary mappings is
    # loaded the only three mappings should be: config, signals, and modules
    # Later versions should throw an error if this is not true.
    # Relevant note: this entire parser is dangerous and does not have any
    # safety checks. It will break badly for malformed yaml data.
    top_level = ["config", "modules", "signals"]
    if not set(model_dict.keys()).issubset(set(top_level)):
        raise RuntimeError("Invalid model definition.")

    # determine model name
    model_name = file.split(".")[0]

    # compute model hash
    hasher = hashlib.sha256()
    hasher.update(json.dumps(model_dict, sort_keys=True).encode())
    model_hash = base64.b64encode(hasher.digest()).decode()

    return model_name, model_hash, model_dict


def __split_env_path(env_var):
    path = os.environ.get(env_var)
    if path:
        path = path.split(os.pathsep)
    else:
        path = []
    return path

def __get_licorice_paths(run_dirname="run"):
    paths = {}
    run_dirname = f"{run_dirname}.lico"

    # correct search paths to work with split
    lico_working_path = __split_env_path("LICORICE_WORKING_PATH")
    lico_template_path = __split_env_path("LICORICE_TEMPLATE_PATH")
    lico_generator_path = __split_env_path("LICORICE_GENERATOR_PATH")
    lico_module_path = __split_env_path("LICORICE_MODULE_PATH")

    # no correction needed for output directories
    lico_output_dir = os.environ.get("LICORICE_OUTPUT_DIR")
    lico_export_dir = os.environ.get("LICORICE_EXPORT_DIR")
    lico_tmp_module_dir = __split_env_path("LICORICE_TMP_MODULE_DIR")
    lico_tmp_output_dir = __split_env_path("LICORICE_TMP_OUTPUT_DIR")

    # search paths may be specified as multiple directories
    if len(lico_working_path) == 0:
        lico_working_path = [os.getcwd()]
        warn(
            "LICORICE_WORKING_PATH env var not set. "
            "Using pwd as working directory.",
            RuntimeWarning,
        )

    dir_path = os.path.dirname(os.path.realpath(__file__))
    paths["templates"] = (
        lico_template_path + [os.path.join(dir_path, "templates")]
    )
    paths["generator"] = (
        lico_generator_path + [os.path.join(dir_path, "generators")]
    )

    paths["modules"] = (
        lico_module_path +
        lico_working_path +
        [os.path.join(dir, "modules") for dir in lico_working_path]
    )

    # output paths must be a single directory
    default_lico_working_path = lico_working_path[0]

    fallback_output_dir = (
        os.path.join(default_lico_working_path, f"{run_dirname}/out")
    )
    if not lico_output_dir and len(lico_working_path) > 1:
        print(
            "Ambiguous output directory specified. Defaulting to "
            f"{fallback_output_dir}."
        )
    paths["output"] = lico_output_dir or fallback_output_dir

    fallback_export_dir = (
        os.path.join(default_lico_working_path, f"{run_dirname}/export")
    )
    if not lico_export_dir and len(lico_working_path) > 1:
        print(
            "Ambiguous export directory specified. Defaulting to "
            f"{fallback_export_dir}."
        )
    paths["export"] = lico_export_dir or fallback_export_dir

    fallback_tmp_module_dir = (
        os.path.join(default_lico_working_path, ".modules")
    )
    if not lico_tmp_module_dir and len(lico_working_path) > 1:
        print(
            "Ambiguous temporary module directory specified. Defaulting to "
            f"{fallback_tmp_module_dir}."
        )
    paths["tmp_modules"] = lico_tmp_module_dir or fallback_tmp_module_dir

    fallback_tmp_output_dir = (
        os.path.join(default_lico_working_path, f"{run_dirname}/.out")
    )
    if not lico_tmp_output_dir and len(lico_working_path) > 1:
        print(
            "Ambiguous temporary output directory specified. Defaulting to "
            f"{fallback_tmp_output_dir}."
        )
    paths["tmp_output"] = lico_tmp_output_dir or fallback_tmp_output_dir

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


def export_model(args):
    model_name, _, _ = __load_and_validate_model(args.model)
    paths = __get_licorice_paths(model_name)
    template_funcs.export(paths, args.confirm)


def generate_model(args):
    model_name, model_hash, model_yaml = __load_and_validate_model(args.model)
    paths = __get_licorice_paths(model_name)
    template_funcs.generate(paths, model_yaml, args.confirm)


def parse_model(args):
    args = __parse_args()
    model_name, model_hash, model_yaml = __load_and_validate_model(args.model)
    paths = __get_licorice_paths(model_name)
    template_funcs.parse(paths, model_yaml, args.confirm)


def compile_model(args):
    model_name, _, _ = __load_and_validate_model(args.model)
    paths = __get_licorice_paths(model_name)

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
    model_name, _, _ = __load_and_validate_model(args.model)
    paths = __get_licorice_paths(model_name)
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
