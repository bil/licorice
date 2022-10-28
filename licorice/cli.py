import argparse
import base64
import copy
import hashlib
import json
import os
import shlex
import subprocess
from distutils.sysconfig import get_python_lib
from functools import lru_cache
from typing import overload
from warnings import warn

import yaml

import licorice.template_funcs as template_funcs
from licorice.utils import __find_in_path, __handle_completed_process

# LiCoRICE paths are of the form f"LICORICE_{path}_PATH"
LICORICE_PATHS = ["WORKING", "TEMPLATE", "GENERATOR", "MODULE", "MODEL"]

# LiCoRICE dirs are of the form f"LICORICE_{path}_DIR"
LICORICE_DIRS = ["OUTPUT", "EXPORT", "TMP_MODULE", "TMP_OUTPUT"]


def __split_path(path):
    if path:
        path = path.split(os.pathsep)
    else:
        path = []
    return path


def __get_licorice_paths(**kwargs):
    # determine model name and output directory
    if type(kwargs["model"]) is str:
        run_dirname = f"{kwargs['model'].split('.')[0]}.lico"
    else:
        run_dirname = "run.lico"

    paths = {}

    # correct search paths to work with split
    lico_paths = {}
    for path_key in LICORICE_PATHS:
        kwarg_paths = __split_path(kwargs.get(f"{path_key.lower()}_path"))
        env_paths = __split_path(os.environ.get(f"LICORICE_{path_key}_PATH"))
        lico_paths[path_key.lower()] = kwarg_paths + env_paths

    # no correction needed for output directories
    lico_dirs = {}
    for dir_key in LICORICE_DIRS:
        lico_dirs[dir_key.lower()] = kwargs.get(
            f"{dir_key.lower()}_dir"
        ) or os.environ.get(f"LICORICE_{dir_key}_DIR")

    # search paths may be specified as multiple directories
    if len(lico_paths["working"]) == 0:
        lico_paths["working"] = [os.getcwd()]
        warn(
            "LICORICE_WORKING_PATH env var not set. "
            "Using pwd as working directory.",
            RuntimeWarning,
        )

    dir_path = os.path.dirname(os.path.realpath(__file__))
    paths["templates"] = lico_paths["template"] + [
        os.path.join(dir_path, "templates")
    ]
    paths["generators"] = lico_paths["generator"] + [
        os.path.join(dir_path, "generators")
    ]

    paths["modules"] = (
        lico_paths["module"]
        + lico_paths["working"]
        + [os.path.join(dir, "modules") for dir in lico_paths["working"]]
    )
    paths["models"] = (
        lico_paths["model"]
        + lico_paths["working"]
        + [os.path.join(dir, "models") for dir in lico_paths["working"]]
    )

    # output paths must be a single directory
    default_lico_working_path = lico_paths["working"][0]

    fallback_output_dir = os.path.join(
        default_lico_working_path, f"{run_dirname}/out"
    )
    if not lico_dirs["output"] and len(lico_paths["working"]) > 1:
        print(
            "Ambiguous output directory specified. Defaulting to "
            f"{fallback_output_dir}."
        )
    paths["output"] = lico_dirs["output"] or fallback_output_dir

    fallback_export_dir = os.path.join(
        default_lico_working_path, f"{run_dirname}/export"
    )
    if not lico_dirs["export"] and len(lico_paths["working"]) > 1:
        print(
            "Ambiguous export directory specified. Defaulting to "
            f"{fallback_export_dir}."
        )
    paths["export"] = lico_dirs["export"] or fallback_export_dir

    fallback_tmp_module_dir = os.path.join(
        default_lico_working_path, ".modules"
    )
    if not lico_dirs["tmp_module"] and len(lico_paths["working"]) > 1:
        print(
            "Ambiguous temporary module directory specified. Defaulting to "
            f"{fallback_tmp_module_dir}."
        )
    paths["tmp_modules"] = lico_dirs["tmp_module"] or fallback_tmp_module_dir

    fallback_tmp_output_dir = os.path.join(
        default_lico_working_path, f"{run_dirname}/.out"
    )
    if not lico_dirs["tmp_output"] and len(lico_paths["working"]) > 1:
        print(
            "Ambiguous temporary output directory specified. Defaulting to "
            f"{fallback_tmp_output_dir}."
        )
    paths["tmp_output"] = lico_dirs["tmp_output"] or fallback_tmp_output_dir

    return paths


def __load_and_validate_model(**kwargs):
    paths = __get_licorice_paths(**kwargs)
    if type(kwargs["model"]) is str:
        file = kwargs["model"]
        filepath = None

        # add working dir and/or extension to config filepath if necessary
        for ext in ["", ".yaml", ".yml"]:
            filepath = __find_in_path(
                paths["models"], file + ext, raise_error=False
            )
            if filepath:
                break

        if not filepath:
            raise FileNotFoundError(
                f"Could not locate model file: {file}. Specify a full path "
                "or set LICORICE_WORKING_PATH and/or other env vars."
            )

        # load model
        with open(filepath, "r") as f:
            try:
                model_dict = yaml.safe_load(f)
            except yaml.YAMLError as exc:
                print(exc)
    else:
        model_dict = copy.deepcopy(kwargs["model"])

    # This assumes that a top level object with three primary mappings is
    # loaded. The only three mappings should be: config, signals, and modules
    # Relevant note: this entire parser is dangerous and does not have any
    # safety checks. It will break badly for malformed yaml data.
    top_level = ["config", "modules", "signals"]
    if not set(model_dict.keys()).issubset(set(top_level)):
        raise RuntimeError("Invalid model definition.")

    # compute model hash
    hasher = hashlib.sha256()
    hasher.update(json.dumps(model_dict, sort_keys=True).encode())
    model_hash = base64.b64encode(hasher.digest()).decode()

    return model_hash, model_dict, paths


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


@lru_cache(maxsize=None)
def __parse_args(input_tuple=None):
    arg_parser = argparse.ArgumentParser(description="LiCoRICE config parser.")
    arg_parser.add_argument(
        "cmd",
        type=str,
        help="LiCoRICE command to run.",
        choices=command_dict.keys(),
    )
    arg_parser.add_argument(
        "model",
        type=str,
        help="YAML model file name to parse. File extension optional.",
    )
    # LiCoRICE CLI only supports simple store_true bools
    arg_parser.add_argument(
        "-y",
        "--confirm",
        action="store_true",
        help="bypass user confirmation on action",
    )
    arg_parser.add_argument(
        "--rt",
        "--realtime",
        action="store_true",
        help="run LiCoRICE with realtime timing guarantees",
    )

    for lico_path in LICORICE_PATHS:
        arg_parser.add_argument(
            f"--{lico_path.lower()}_path",
            type=str,
            help=(
                "Overrides LiCoRICE PATH environment variable "
                f"LICORICE_{lico_path}_PATH"
            ),
        )

    for lico_dir in LICORICE_DIRS:
        arg_parser.add_argument(
            f"--{lico_dir.lower()}_dir",
            type=str,
            help=(
                "Overrides LiCoRICE DIR environment variable "
                f"LICORICE_{lico_dir}_DIR"
            ),
        )

    if input_tuple:
        args = arg_parser.parse_args(input_tuple)
    else:
        args = arg_parser.parse_args()

    return args


def __parse_kwargs(func_name, model, **kwargs):
    model_dict = None
    if type(model) is dict:
        model_dict = model
        model = "placeholder"

    input_args = [func_name, model]
    for k, v in kwargs.items():
        # skip value on simple store_true bools
        if type(v) is bool:
            if v:
                input_args.append(f"--{k}")
        else:
            input_args.append(f"--{k}")
            input_args.append(str(v))

    args = __parse_args(tuple(input_args))
    kwargs = vars(args)
    if model_dict:
        kwargs["model"] = model_dict

    return kwargs


def __export_model(**kwargs):
    _, _, paths = __load_and_validate_model(**kwargs)
    template_funcs.export(paths, kwargs["confirm"])


@overload
def export_model(model: str, **kwargs) -> None:
    ...


@overload  # noqa: E302
def export_model(model: dict, **kwargs) -> None:
    ...


def export_model(model, **kwargs):  # noqa: E302
    """Export a LiCoRICE model.

    This function wraps the core functionality of the LiCoRICE CLI `export`
    command, but allows users to pass in either a YAML model file string or a
    full dict detailing the model as well as any CLI flags as keyword
    arguments.

    Args:
        model (str): Filename of LiCoRICE model accessible through default or
            included paths. `.yaml` and `.yml` file extensions are optional.
        model (dict): LiCoRICE model as a dict. Must adhere to YAML config
            reference and can be loaded in from a YAML file or created
            manually.

    Keyword Args:
        kwargs (dict): Extra LiCoRICE arguments.

    Returns:
        None
    """
    kwargs = __parse_kwargs("export", model, **kwargs)
    __export_model(**kwargs)


def __generate_model(**kwargs):
    model_hash, model_yaml, paths = __load_and_validate_model(**kwargs)
    template_funcs.generate(paths, model_yaml, kwargs["confirm"])


@overload
def generate_model(model: str, **kwargs) -> None:
    ...


@overload  # noqa: E302
def generate_model(model: dict, **kwargs) -> None:
    ...


def generate_model(model, **kwargs):  # noqa: E302
    """Generate user code scaffolds from model.

    This function wraps the core functionality of the LiCoRICE CLI `generate`
    command, but allows users to pass in either a YAML model file string or a
    full dict detailing the model as well as any CLI flags as keyword
    arguments.

    Args:
        model (str): Filename of LiCoRICE model accessible through default or
            included paths. `.yaml` and `.yml` file extensions are optional.
        model (dict): LiCoRICE model as a dict. Must adhere to YAML config
            reference and can be loaded in from a YAML file or created
            manually.

    Keyword Args:
        kwargs (dict): Extra LiCoRICE arguments.

    Returns:
        None
    """
    kwargs = __parse_kwargs("generate", model, **kwargs)
    __generate_model(**kwargs)


def __parse_model(**kwargs):
    model_hash, model_yaml, paths = __load_and_validate_model(**kwargs)
    template_funcs.parse(paths, model_yaml, kwargs["confirm"])


@overload
def parse_model(model: str, **kwargs) -> None:
    ...


@overload  # noqa: E302
def parse_model(model: dict, **kwargs) -> None:
    ...


def parse_model(model, **kwargs):  # noqa: E302
    """Parse a given LiCoRICE model.

    This function wraps the core functionality of the LiCoRICE CLI `parse`
    command, but allows users to pass in either a YAML model file string or a
    full dict detailing the model as well as any CLI flags as keyword
    arguments.

    Args:
        model (str): Filename of LiCoRICE model accessible through default or
            included paths. `.yaml` and `.yml` file extensions are optional.
        model (dict): LiCoRICE model as a dict. Must adhere to YAML config
            reference and can be loaded in from a YAML file or created
            manually.

    Keyword Args:
        kwargs (dict): Extra LiCoRICE arguments.

    Returns:
        None
    """
    kwargs = __parse_kwargs("parse", model, **kwargs)
    __parse_model(**kwargs)


def __compile_model(**kwargs):
    _, _, paths = __load_and_validate_model(**kwargs)

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


@overload
def compile_model(model: str, **kwargs) -> None:
    ...


@overload  # noqa: E302
def compile_model(model: dict, **kwargs) -> None:
    ...


def compile_model(model, **kwargs):  # noqa: E302
    """Compile a given LiCoRICE model.

    This function wraps the core functionality of the LiCoRICE CLI `compile`
    command, but allows users to pass in either a YAML model file string or a
    full dict detailing the model as well as any CLI flags as keyword
    arguments.

    Args:
        model (str): Filename of LiCoRICE model accessible through default or
            included paths. `.yaml` and `.yml` file extensions are optional.
        model (dict): LiCoRICE model as a dict. Must adhere to YAML config
            reference and can be loaded in from a YAML file or created
            manually.

    Keyword Args:
        kwargs (dict): Extra LiCoRICE arguments.

    Returns:
        None
    """

    kwargs = __parse_kwargs("compile", model, **kwargs)
    __compile_model(**kwargs)


def __run_model(**kwargs):
    _, _, paths = __load_and_validate_model(**kwargs)
    os_env = os.environ.copy()
    os_env["PYTHONPATH"] = get_python_lib()
    if kwargs["rt"]:
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


@overload
def run_model(model: str, **kwargs) -> None:
    ...


@overload  # noqa: E302
def run_model(model: dict, **kwargs) -> None:
    ...


def run_model(model, **kwargs):
    """Run the given compiled LiCoRICE model.

    This function wraps the core functionality of the LiCoRICE CLI `run`
    command, but allows users to pass in either a YAML model file string or a
    full dict detailing the model as well as any CLI flags as keyword
    arguments.

    Args:
        model (str): Filename of LiCoRICE model accessible through default or
            included paths. `.yaml` and `.yml` file extensions are optional.
        model (dict): LiCoRICE model as a dict. Must adhere to YAML config
            reference and can be loaded in from a YAML file or created
            manually.

    Keyword Args:
        kwargs (dict): Extra LiCoRICE arguments.

    Returns:
        None
    """

    kwargs = __parse_kwargs("run", model, **kwargs)
    __run_model(**kwargs)


def __go(**kwargs):
    __parse_model(**kwargs)
    __compile_model(**kwargs)
    __run_model(**kwargs)


@overload
def go(model: str, **kwargs) -> None:
    ...


@overload  # noqa: E302
def go(model: dict, **kwargs) -> None:
    ...


def go(model, **kwargs):  # noqa: E302
    """Peform LiCoRICE parse, compile, and run in succession.

    This function wraps the core functionality of the LiCoRICE CLI `go`
    command, but allows users to pass in either a YAML model file string or a
    full dict detailing the model as well as any CLI flags as keyword
    arguments.

    Args:
        model (str): Filename of LiCoRICE model accessible through default or
            included paths. `.yaml` and `.yml` file extensions are optional.
        model (dict): LiCoRICE model as a dict. Must adhere to YAML config
            reference and can be loaded in from a YAML file or created
            manually.

    Keyword Args:
        kwargs (dict): Extra LiCoRICE arguments.

    Returns: None
    """
    kwargs = __parse_kwargs("go", model, **kwargs)
    __go(**kwargs)


command_dict = {
    "generate": __generate_model,
    "parse": __parse_model,
    "compile": __compile_model,
    "run": __run_model,
    "go": __go,
    "export": __export_model,
}


def main():
    args = __parse_args()
    kwargs = vars(args)

    command_dict[args.cmd](**kwargs)


if __name__ == "__main__":

    main()
