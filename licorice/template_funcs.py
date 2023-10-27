import copy
import os
import platform
import shutil
import string
import subprocess
import sys
import warnings
from ast import literal_eval
from distutils.sysconfig import get_config_var, get_python_lib
from sysconfig import get_paths

import jinja2
import numpy as np
from toposort import toposort

from licorice.cpu_affinity import determine_cpu_affinity
from licorice.utils import __find_in_path, __handle_completed_process

# available path constants
# paths['templates']
# paths['generators']
# paths['modules']
# paths['output']
# paths['export']
# paths['tmp_modules']
# paths['tmp_output']

TEMPLATE_MODULE_C = "module.c.j2"
TEMPLATE_MODULE_PY = "module.pyx.j2"
TEMPLATE_SINK_PY = "sink.pyx.j2"
TEMPLATE_SINK_C = "sink.c.j2"
TEMPLATE_SOURCE_PY = "source.pyx.j2"
TEMPLATE_SOURCE_C = "source.c.j2"

TEMPLATE_MAKEFILE = "Makefile.j2"
TEMPLATE_TIMER = "timer.c.j2"
TEMPLATE_CONSTANTS = "constants.h.j2"
TEMPLATE_NUMBA = "numba_pycc.j2"

G_TEMPLATE_MODULE_CODE_PY = "module_code_py.j2"
G_TEMPLATE_SOURCE_PARSER_PY = "source_parser_py.j2"
G_TEMPLATE_SINK_PARSER_PY = "sink_parser_py.j2"
G_TEMPLATE_CONSTRUCTOR_PY = "constructor_py.j2"
G_TEMPLATE_DESTRUCTOR_PY = "destructor_py.j2"
G_TEMPLATE_MODULE_CODE_C = "module_code_c.j2"
G_TEMPLATE_SOURCE_PARSER_C = "source_parser_c.j2"
G_TEMPLATE_SINK_PARSER_C = "sink_parser_c.j2"
G_TEMPLATE_CONSTRUCTOR_C = "constructor_c.j2"
G_TEMPLATE_DESTRUCTOR_C = "destructor_c.j2"

OUTPUT_MAKEFILE = "Makefile"
OUTPUT_TIMER = "timer.c"
OUTPUT_CONSTANTS = "constants.h"

BUF_VARS_LEN = 16
# TODO maybe a cleaner way to have a default value for this
HISTORY_DEFAULT = 5000


# change dtype to C format
def fix_dtype(dtype):
    if "int" in dtype and not dtype.endswith("_t"):
        return dtype + "_t"
    elif dtype == "float64" or dtype == "double":
        return "double"
    elif dtype == "float32" or dtype == "float":
        return "float"
    elif dtype == "object":
        return "void"
    raise ValueError(f"Unsupported dtype: {dtype}")


# get number of bytes for a given ctype
def bytes_for_ctype(ctype):
    if "int" in ctype:
        return int(ctype.strip(string.ascii_letters)[:-1]) // 8
    elif ctype == "double":
        return 8
    elif ctype == "float":
        return 4
    # TODO handle void
    else:
        raise ValueError(f"Unsupported ctype: {ctype}")


# change dtype to msgpack format
def fix_dtype_msgpack(dtype):
    if dtype in ["float32", "float"]:
        dtype = "float"
    if dtype in ["float64", "double"]:
        dtype = "double"
    return dtype


# create signal dependency graph and topological order variables
def create_dependency_info(modules, names):
    dep_info = {}
    dep_info["graph"] = {}
    for idx, name in enumerate(names):
        args = modules.get(name)
        deps = set()
        if not args:
            if "async_writer" in name:
                deps = deps.union(
                    {names.index(name[: -1 - len("async_writer")])}
                )
        elif type(args.get("in")) is list:
            for in_sig in args["in"]:
                for dep_idx, dep_name in enumerate(names):
                    dep_args = modules.get(dep_name)
                    if not dep_args:
                        continue
                    for out_sig in dep_args["out"]:
                        if in_sig == out_sig:
                            deps = deps.union({dep_idx})
        else:
            if (async_reader_name := f"{name}_async_reader") in names:
                deps = deps.union({names.index(async_reader_name)})

        dep_info["graph"][idx] = deps

    dep_info["topo"] = list(map(list, list(toposort(dep_info["graph"]))))
    dep_info["widths"] = list(map(len, dep_info["topo"]))
    dep_info["height"] = len(dep_info["topo"])
    dep_info["max_width"] = (
        0 if len(dep_info["widths"]) == 0 else max(dep_info["widths"])
    )
    return dep_info


# load, setup, and write template
def do_jinja(template_path, out_path, **data):
    template = jinja2.Template(open(template_path, "r").read())
    out_f = open(out_path, "w")
    out_f.write(template.render(data))
    out_f.close()


# generate empty templates for modules, parsers, constructors, and destructors
def generate(paths, config, confirmed):
    print("Generating modules...\n")

    if len(paths["modules"]) > 1:
        print(
            "Ambiguous module directory specified. Defaulting to "
            f"{paths['modules'][0]}."
        )

    modules_path = paths["modules"][0]

    # TODO update generate
    # TODO keeping this directory around causes an error where old generated
    # files can be copied over even after they're removed from the model
    # if os.path.exists(modules_path):
    #     if not confirmed:
    #         while True:
    #             sys.stdout.write("Ok to remove old module directory? ")
    #             choice = input().lower()
    #             if choice == "y":
    #                 break
    #             elif choice == "n":
    #                 print(
    #                     "Could not complete generation. "
    #                     "Backup old modules if necessary and try again."
    #                 )
    #                 sys.exit()
    #             else:
    #                 print("Please respond with 'y' or 'n'.")
    #     if os.path.exists(paths["tmp_modules"]):
    #         shutil.rmtree(paths["tmp_modules"])
    #     shutil.move(modules_path, paths["tmp_modules"])
    #     print("Moved " + modules_path + " to ") + paths["tmp_modules"]
    #     shutil.rmtree(modules_path, ignore_errors=True)
    #     print("Removed old output directory.\n")

    # os.mkdir(modules_path)

    print("Generated modules:")

    # TODO rename to runners
    modules = {}
    if "modules" in config and config["modules"]:
        modules = config["modules"]

    for module_key, module_val in iter(modules.items()):
        if isinstance(module_val.get("in"), dict):
            # source
            print(" - " + module_key + " (source)")

            if module_val["language"] == "python":
                parse_template = G_TEMPLATE_SOURCE_PARSER_PY
                construct_template = G_TEMPLATE_CONSTRUCTOR_PY
                destruct_template = G_TEMPLATE_DESTRUCTOR_PY
                extension = ".py"
            else:
                parse_template = G_TEMPLATE_SOURCE_PARSER_C
                construct_template = G_TEMPLATE_CONSTRUCTOR_C
                destruct_template = G_TEMPLATE_DESTRUCTOR_C
                extension = ".c"

            # generate source parser template
            if "parser" in module_val and module_val["parser"]:
                if module_val["parser"] is True:
                    module_val["parser"] = module_key + "_parser"
                output_path = os.path.join(
                    modules_path, module_val["parser"] + extension
                )
                if not os.path.exists(output_path):
                    print("   - " + module_val["parser"] + " (parser)")
                    do_jinja(
                        __find_in_path(paths["generators"], parse_template),
                        output_path,
                    )

            # generate source constructor template
            if "constructor" in module_val and module_val["constructor"]:
                if module_val["constructor"] is True:
                    module_val["constructor"] = module_key + "_constructor"
                output_path = os.path.join(
                    modules_path,
                    module_val["constructor"] + extension,
                )
                if not os.path.exists(output_path):
                    print(
                        "   - " + module_val["constructor"] + " (constructor)"
                    )
                    do_jinja(
                        __find_in_path(
                            paths["generators"], construct_template
                        ),
                        output_path,
                    )

            # generate source destructor template
            if "destructor" in module_val and module_val["destructor"]:
                if module_val["destructor"] is True:
                    module_val["destructor"] = module_key + "_destructor"
                output_path = os.path.join(
                    modules_path, module_val["destructor"] + extension
                )
                if not os.path.exists(output_path):
                    print("   - " + module_val["destructor"] + " (destructor)")
                    do_jinja(
                        __find_in_path(paths["generators"], destruct_template),
                        output_path,
                    )

        elif isinstance(module_val.get("out"), dict):
            # sink
            print(" - " + module_key + " (sink)")

            if module_val["language"] == "python":
                parse_template = G_TEMPLATE_SOURCE_PARSER_PY
                construct_template = G_TEMPLATE_CONSTRUCTOR_PY
                destruct_template = G_TEMPLATE_DESTRUCTOR_PY
                extension = ".py"
            else:
                parse_template = G_TEMPLATE_SOURCE_PARSER_C
                construct_template = G_TEMPLATE_CONSTRUCTOR_C
                destruct_template = G_TEMPLATE_DESTRUCTOR_C
                extension = ".c"

            if "parser" in module_val and module_val["parser"]:
                if module_val["parser"] is True:
                    module_val["parser"] = module_key + "_parser"
                output_path = os.path.join(
                    modules_path, module_val["parser"] + extension
                )
                if not os.path.exists(output_path):
                    print("   - " + module_val["parser"] + " (parser)")
                    do_jinja(
                        __find_in_path(paths["generators"], parse_template),
                        output_path,
                    )

            if "constructor" in module_val and module_val["constructor"]:
                if module_val["constructor"] is True:
                    module_val["constructor"] = module_key + "_constructor"
                output_path = os.path.join(
                    modules_path,
                    module_val["constructor"] + extension,
                )
                if not os.path.exists(output_path):
                    print(
                        "   - " + module_val["constructor"] + " (constructor)"
                    )
                    do_jinja(
                        __find_in_path(
                            paths["generators"], construct_template
                        ),
                        output_path,
                    )

            if "destructor" in module_val and module_val["destructor"]:
                if module_val["destructor"] is True:
                    module_val["destructor"] = module_key + "_destructor"
                output_path = os.path.join(
                    modules_path, module_val["destructor"] + extension
                )
                if not os.path.exists(output_path):
                    print("   - " + module_val["destructor"] + " (destructor)")
                    do_jinja(
                        __find_in_path(paths["generators"], destruct_template),
                        output_path,
                    )

        else:
            # module
            print(f" - {module_key}")

            if module_val["language"] == "python":
                code_template = G_TEMPLATE_MODULE_CODE_PY
                construct_template = G_TEMPLATE_CONSTRUCTOR_PY
                destruct_template = G_TEMPLATE_DESTRUCTOR_PY
                extension = ".py"
            else:
                code_template = G_TEMPLATE_MODULE_CODE_C
                construct_template = G_TEMPLATE_CONSTRUCTOR_C
                destruct_template = G_TEMPLATE_DESTRUCTOR_C
                extension = ".c"

            output_path = os.path.join(modules_path, module_key + ".py")
            if not os.path.exists(output_path):
                do_jinja(
                    __find_in_path(paths["generators"], code_template),
                    output_path,
                    name=module_key,
                    in_sig=module_val.get("in"),
                    out_sig=module_val.get("out"),
                )

            if "constructor" in module_val and module_val["constructor"]:
                if module_val["constructor"] is True:
                    module_val["constructor"] = module_key + "_constructor"
                output_path = os.path.join(
                    modules_path,
                    module_val["constructor"] + extension,
                )
                if not os.path.exists(output_path):
                    print(
                        "   - " + module_val["constructor"] + " (constructor)"
                    )
                    do_jinja(
                        __find_in_path(
                            paths["generators"], construct_template
                        ),
                        output_path,
                    )

            if "destructor" in module_val and module_val["destructor"]:
                if module_val["destructor"] is True:
                    module_val["destructor"] = module_key + "_destructor"
                output_path = os.path.join(
                    modules_path, module_val["destructor"] + extension
                )
                if not os.path.exists(output_path):
                    print("   - " + module_val["destructor"] + " (destructor)")
                    do_jinja(
                        __find_in_path(paths["generators"], destruct_template),
                        output_path,
                    )


def parse(paths, config, confirmed):
    print("Parsing")

    config = copy.deepcopy(config)

    platform_system = platform.system()

    # TODO determine if we want to keep this
    # save unmodified config to pass to user-space code
    # unmodified_config = copy.deepcopy(config)

    # set default values in config
    if not config.get("config"):
        config["config"] = {}
    if not config["config"].get("num_ticks"):
        config["config"]["num_ticks"] = -1
    if not config["config"].get("tick_len"):
        config["config"]["tick_len"] = 1000
    if not config["config"].get("new_db_num_ticks"):
        config["config"]["new_db_num_ticks"] = (
            60000000 // config["config"]["tick_len"]
        )  # default to approximately one minute
    if not config["config"].get("sql_logger_flush"):
        config["config"]["sql_logger_flush"] = 1000

    modules = {}
    if "modules" in config and config["modules"]:
        modules = config["modules"]

    signals = {}
    if "signals" in config and config["signals"]:
        signals = config["signals"]

    # set up output directory
    if os.path.exists(paths["output"]):
        if not confirmed:
            while True:
                sys.stdout.write("Ok to remove old output directory? ")
                choice = input().lower()
                if choice == "y":
                    break
                elif choice == "n":
                    sys.exit(
                        "Could not complete parsing. Backup old output "
                        "directory if necessary and try again."
                    )
                else:
                    print("Please respond with 'y' or 'n'.")
            print()
        if os.path.exists(paths["tmp_output"]):
            shutil.rmtree(paths["tmp_output"])
        shutil.move(paths["output"], paths["tmp_output"])
        print("Moved " + paths["output"] + " to " + paths["tmp_output"])
        shutil.rmtree(paths["output"], ignore_errors=True)
        print("Removing old output directory.\n")

    # copy helper files to output path
    for template_path in paths["templates"]:
        shutil.copytree(
            template_path,
            paths["output"],
            ignore=shutil.ignore_patterns(("*.j2")),
            dirs_exist_ok=True,
        )

    # set up signal helper variables
    internal_signals = list(signals or [])  # list of numpy signal names
    external_signals = []  # list of external signal names

    # TODO need to assert that source output buffer sizes match module input
    # sizes for no parser (and vice versa for sinks). check for parser case?
    for signal_name, signal_args in iter(signals.items()):
        # store 1D array shape as length of array
        a = np.empty(literal_eval(str(signal_args["shape"])))
        a = a.squeeze()
        if len(a.shape) == 1:
            signal_args["shape"] = a.shape[0]

        signal_args["sig_shape"] = str(signal_args["shape"]).partition("(")[2]
        if signal_args["sig_shape"] == "":
            signal_args["sig_shape"] = str(signal_args["shape"]) + ")"

        if "max_packets_per_tick" not in signal_args:
            # TODO top-level signals should potentially inherit from source
            signal_args["max_packets_per_tick"] = 1

        # TODO test setting this to low values
        if "history" not in signal_args:
            signal_args["history"] = HISTORY_DEFAULT

        if signal_args["history"] < signal_args["max_packets_per_tick"]:
            signal_args["history"] = signal_args["max_packets_per_tick"]
            warnings.warn("history must be at least max_packets_per_tick.")

        signal_args["sig_shape"] = (
            f"({signal_args['history']}," f"{signal_args['sig_shape']}"
        )
        signal_args["buf_tot_numel"] = np.prod(
            np.array(literal_eval(str(signal_args["sig_shape"])))
        )
        signal_args["packet_size"] = np.prod(
            np.array(literal_eval(str(signal_args["shape"])))
        )
        signal_args["ctype"] = fix_dtype(signal_args["dtype"])
        signal_args["dtype_msgpack"] = fix_dtype_msgpack(signal_args["dtype"])
        signal_args["bytes"] = bytes_for_ctype(signal_args["ctype"])

        signal_args["buf_size_bytes"] = (
            signal_args["max_packets_per_tick"]
            * signal_args["packet_size"]
            * signal_args["bytes"]
        )

        if "latency" not in signal_args:
            signal_args["latency"] = 0

    for module_key, module_val in iter(modules.items()):
        ext_sig = None
        if (
            "in" in module_val
            and isinstance(module_val["in"], dict)
            and "name" in module_val["in"]
        ):  # source
            ext_sig = module_val["in"]

            max_packets_per_tick = ext_sig["schema"].get(
                "max_packets_per_tick"
            )
            ext_sig["schema"]["max_packets_per_tick"] = max_packets_per_tick
            if max_packets_per_tick is None:
                if ext_sig.get("async"):
                    ext_sig["schema"]["max_packets_per_tick"] = 0
                else:
                    ext_sig["schema"]["max_packets_per_tick"] = 1
        elif (
            "out" in module_val
            and isinstance(module_val["out"], dict)
            and "name" in module_val["out"]
        ):  # sink
            ext_sig = module_val["out"]
        else:  # module
            continue
        external_signals.append(ext_sig["name"])
        signals[ext_sig["name"]] = ext_sig

    sigkeys = set(signals)

    # process modules
    sem_location = 0
    sig_sem_dict = {}
    num_sem_sigs = 0

    child_dicts = []  # list of dicts to be converted to structs in timer
    module_names = []  # list of module names
    source_names = []  # list of source names
    async_readers_dict = {}  # dict of source: async_readers
    sink_names = []  # list of sink names
    async_writers_dict = {}  # dict of sink: async_writers
    source_outputs = {}
    in_signals = {}
    out_signals = {}
    sink_in_sig_nums = []

    # TODO should order of runner names be in topological order?
    # For example, forces correct teardown order in timer
    runner_names = list(modules)
    assert len(runner_names) == len(set(runner_names))

    compile_for_line = False
    for module_key, module_val in iter(modules.items()):

        if (
            "in" in module_val
            and isinstance(module_val["in"], dict)
            and module_val["in"]["name"] in external_signals
        ):
            # source
            source_names.append(module_key)
            if module_val["in"].get("async") or False:
                async_readers_dict[module_key] = f"{module_key}_async_reader"
            for sig in module_val["out"]:
                source_outputs[sig] = 0
            in_sig_name = module_val["in"]["name"]
            assert "type" in signals[in_sig_name]["args"]
            in_signals[in_sig_name] = signals[in_sig_name]["args"]["type"]

            out_sig_schema_num = 0
            for sig, args in iter(
                {
                    x: signals[x] for x in (sigkeys & set(module_val["out"]))
                }.items()
            ):
                # TODO, should max_packets_per_tick be copied over?
                if "schema" in args:
                    out_sig_schema_num += 1
                else:
                    args["schema"] = signals[module_val["in"]["name"]][
                        "schema"
                    ]
            if out_sig_schema_num > 0:
                assert out_sig_schema_num == len(list(out_signals))

        elif (
            "out" in module_val
            and isinstance(module_val["out"], dict)
            and module_val["out"]["name"] in external_signals
        ):
            # sink
            sink_names.append(module_key)
            if module_val["out"].get("async") or False:
                async_writers_dict[module_key] = f"{module_key}_async_writer"
            out_sig_name = module_val["out"]["name"]
            assert "type" in signals[out_sig_name]["args"]
            out_signals[out_sig_name] = signals[out_sig_name]["args"]["type"]
            if out_signals[out_sig_name] in ["line"]:
                compile_for_line = True
        else:
            # module
            if "in" not in module_val or not module_val["in"]:
                module_val["in"] = []
            if "out" not in module_val or not module_val["out"]:
                module_val["out"] = []
            if not isinstance(module_val["in"], list):
                module_val["in"] = [module_val["in"]]
            if not isinstance(module_val["out"], list):
                module_val["out"] = [module_val["out"]]
            module_names.append(module_key)

    # create semaphore signal mapping w/ format {'sig_name': ptr_offset}
    for sig_name in internal_signals:
        if sig_name not in sig_sem_dict:
            sig_sem_dict[sig_name] = sem_location
            sem_location += 1
    num_sem_sigs = len(sig_sem_dict)

    # TODO make this part of parser validation
    assert set(runner_names) == set(source_names + module_names + sink_names)
    m_info = {}  # model info
    m_info["num_sources"] = len(source_names)
    m_info["num_modules"] = len(module_names)
    m_info["num_sinks"] = len(sink_names)
    m_info["num_runners"] = len(runner_names)

    async_reader_names = list(async_readers_dict.values())
    async_writer_names = list(async_writers_dict.values())
    num_async_readers = len(async_reader_names)
    num_async_writers = len(async_writer_names)
    # num_async_procs = num_async_readers + num_async_writers

    child_names = async_reader_names + runner_names + async_writer_names

    for i, name in enumerate(child_names):
        is_async = False
        if name in source_names:
            child_type = "source"
        elif name in async_reader_names:
            child_type = "async_reader"
            is_async = True
        elif name in module_names:
            child_type = "module"
        elif name in sink_names:
            child_type = "sink"
        elif name in async_writer_names:
            child_type = "async_writer"
            is_async = True
        child_dicts.append(
            {"name": name, "type": child_type, "async": is_async}
        )

    # determine dependency directed acyclic graphs, perform a topological
    # sort, and determine the size of the topology

    # all children including async
    child_dep_info = create_dependency_info(modules, child_names)

    # sources sinks and modules (runners)
    runner_dep_info = create_dependency_info(modules, runner_names)

    # only modules
    module_dep_info = create_dependency_info(modules, module_names)

    affinity_info = determine_cpu_affinity(
        m_info,
        config,
        modules,
        module_names,
        child_dicts,
        runner_dep_info,
        module_dep_info,
    )

    print(f'LiCoRICE will run on {affinity_info["num_cores_used"]} core(s).')

    # print("system input and output signals")
    print("Inputs: ")
    for sig_name, sig_type in iter(in_signals.items()):
        print(" - " + sig_name + ": " + sig_type)
    print("Outputs: ")
    for sig_name, sig_type in iter(out_signals.items()):
        print(" - " + sig_name + ": " + sig_type)

    # parse sources, sinks and modules
    print("Modules: ")
    for name in runner_names:
        # get module info
        module_val = modules[name]
        module_language = module_val["language"]  # language must be specified

        # parse source
        if name in source_names:
            print(" - " + name + " (source)")

            if module_language == "python":
                template = TEMPLATE_SOURCE_PY
                # TODO split cython and python?
                in_extensions = [".pyx.j2", ".pyx", ".py.j2", ".py"]
                out_extension = ".pyx"
            else:
                raise NotImplementedError()
                template = TEMPLATE_SOURCE_C
                in_extensions = [".c.j2", ".c"]
                out_extension = ".c"
            in_signal = signals[module_val["in"]["name"]]
            out_signals = {
                x: signals[x] for x in (sigkeys & set(module_val["out"]))
            }
            out_sig_nums = {
                x: internal_signals.index(x) for x in list(out_signals)
            }
            has_parser = "parser" in module_val and module_val["parser"]
            if not has_parser:
                assert len(out_signals) == 1

            default_params = (
                in_signal["schema"]["default"]
                if (in_signal["args"]["type"] == "default")
                else None
            )

            in_dtype = in_signal["schema"]["data"]["dtype"]
            in_dtype = fix_dtype(in_dtype)
            out_sig_types = {}
            for sig, args in iter(out_signals.items()):
                dtype = args["dtype"]
                dtype = fix_dtype(dtype)
                out_sig_types[sig] = dtype
                if not has_parser:
                    assert (
                        in_dtype == dtype
                    )  # out_signals has length 1 for no parser
                args["packet_size"] = np.prod(
                    np.array(literal_eval(str(args["shape"])))
                )

            sig_sems = []
            for out_sig in module_val["out"]:
                sig_sems.append((out_sig, sig_sem_dict[out_sig]))

            out_sig_dependency_info = {}
            for out_sig in module_val["out"]:
                for tmp_name in runner_names:
                    mod = modules[tmp_name]
                    for in_sig in mod["in"]:
                        if in_sig == out_sig:
                            if out_sig in out_sig_dependency_info:
                                out_sig_dependency_info[out_sig] += 1
                            else:
                                out_sig_dependency_info[out_sig] = 1

            for out_sig in out_sig_dependency_info:
                out_sig_dependency_info[out_sig] = (
                    out_sig_dependency_info[out_sig],
                    sig_sem_dict[out_sig],
                )

            driver_template_name = f'{in_signal["args"]["type"]}'
            driver_output_name = f"{name}_{driver_template_name}"
            async_source = name in async_readers_dict.keys()
            async_reader_name = async_readers_dict.get(name)
            source_template_kwargs = {
                "name": name,
                "source_num": source_names.index(name),
                "config": config,
                "source_args": module_val,
                "has_parser": has_parser,
                "async": async_source,
                "async_reader_name": async_reader_name,
                "async_reader_num": (
                    async_reader_names.index(async_reader_name)
                    if async_source
                    else None
                ),
                "in_sig_name": module_val["in"]["name"],
                "in_signal": in_signal,
                "out_signals": out_signals,
                "out_signal_name": (
                    None if (has_parser) else list(out_signals)[0]
                ),
                "out_signal_type": (
                    None
                    if (has_parser)
                    else out_sig_types[list(out_signals)[0]]
                ),
                "out_sig_nums": out_sig_nums,
                "out_sig_dependency_info": out_sig_dependency_info,
                "default_params": default_params,
                "num_sem_sigs": num_sem_sigs,
                "sig_sems": sig_sems,
                "in_dtype": in_dtype,
                "sig_types": out_sig_types,
                "buf_vars_len": BUF_VARS_LEN,
                "py_maj_version": sys.version_info[0],
                "platform_system": platform_system,
            }

            parser_code = ""
            if has_parser:
                if module_val["parser"] is True:
                    module_val["parser"] = name + "_parser"
                with open(
                    __find_in_path(
                        paths["modules"],
                        [
                            f"{module_val['parser']}{ext}"
                            for ext in in_extensions
                        ],
                    ),
                    "r",
                ) as f:
                    parser_code = f.read()
                    parser_code = parser_code.replace("\n", "\n  ")
                    parser_code = jinja2.Template(parser_code)
                    parser_code = parser_code.render(**source_template_kwargs)

            construct_code = ""
            if "constructor" in module_val and module_val["constructor"]:
                if module_val["constructor"] is True:
                    module_val["constructor"] = name + "_constructor"
                with open(
                    __find_in_path(
                        paths["modules"],
                        [
                            f"{module_val['constructor']}{ext}"
                            for ext in in_extensions
                        ],
                    ),
                    "r",
                ) as f:
                    construct_code = f.read()
                    construct_code = jinja2.Template(construct_code)
                    construct_code = construct_code.render(
                        **source_template_kwargs
                    )

            destruct_code = ""
            if "destructor" in module_val and module_val["destructor"]:
                if module_val["destructor"] is True:
                    module_val["destructor"] = name + "_destructor"
                with open(
                    __find_in_path(
                        paths["modules"],
                        [
                            f"{module_val['destructor']}{ext}"
                            for ext in in_extensions
                        ],
                    ),
                    "r",
                ) as f:
                    destruct_code = f.read()
                    destruct_code = destruct_code.replace("\n", "\n  ")
                    destruct_code = jinja2.Template(destruct_code)
                    destruct_code = destruct_code.render(
                        **source_template_kwargs
                    )

            source_template_kwargs.update(
                {
                    "parser_code": parser_code,
                    "construct_code": construct_code,
                    "destruct_code": destruct_code,
                }
            )

            # parse source driver
            driver_template_file = f"{driver_template_name}.pyx.j2"
            driver_output_path = os.path.join(
                paths["output"], f"source_drivers/{driver_output_name}.pyx"
            )
            do_jinja(
                __find_in_path(
                    paths["templates"],
                    f"source_drivers/{driver_template_file}",
                ),
                driver_output_path,
                **source_template_kwargs,
            )
            with open(driver_output_path, "r") as f:
                driver_code = f.read()
            driver_code = {
                code.partition("\n")[0].strip(): code.partition("\n")[2]
                for code in filter(
                    None, driver_code.split("# __DRIVER_CODE__")
                )
            }

            # parse source async reader if async
            if async_source:
                do_jinja(
                    __find_in_path(paths["templates"], template),
                    os.path.join(
                        paths["output"], async_reader_name + out_extension
                    ),
                    driver_code=driver_code,
                    is_main_process=False,
                    is_reader=True,
                    **source_template_kwargs,
                )

            # parse source template
            do_jinja(
                __find_in_path(paths["templates"], template),
                os.path.join(paths["output"], name + out_extension),
                driver_code=(None if async_source else driver_code),
                is_main_process=True,
                is_reader=(not async_source),
                **source_template_kwargs,
            )

        # parse sink
        elif name in sink_names:
            print(" - " + name + " (sink)")
            if module_language == "python":
                template = TEMPLATE_SINK_PY
                # TODO split cython and python?
                in_extensions = [".pyx.j2", ".pyx", ".py.j2", ".py"]
                out_extension = ".pyx"
            else:
                raise NotImplementedError()
                template = TEMPLATE_SINK_C
                in_extensions = [".c.j2", ".c"]
                out_extension = ".c"
            in_signals = {}
            if "in" in module_val:
                in_signals = {
                    x: signals[x] for x in (sigkeys & set(module_val["in"]))
                }
            in_sig_nums = {
                x: internal_signals.index(x) for x in list(in_signals)
            }
            sink_in_sig_nums.extend(in_sig_nums.values())
            out_signal = signals[module_val["out"]["name"]]
            has_parser = "parser" in module_val and module_val["parser"]

            if not has_parser:
                # TODO this validation should happen in the driver code
                if len(in_signals) != 1:
                    warnings.warn(
                        "No parser specified for multiple sink input signals."
                        "Parser must happen in sink"
                    )

            in_sig_sems = []
            for sig, args in iter(in_signals.items()):
                # store the signal name in 0 and location of sem in 1
                in_sig_sems.append((sig, sig_sem_dict[sig]))

            out_dtype = None
            if "schema" in out_signal:
                out_dtype = out_signal["schema"]["data"]["dtype"]
                out_dtype = fix_dtype(out_dtype)
            in_sig_types = {}
            for sig, args in iter(in_signals.items()):
                dtype = args["dtype"]
                dtype = fix_dtype(dtype)
                in_sig_types[sig] = dtype
                if not has_parser and out_dtype:
                    assert (
                        out_dtype == dtype
                    )  # in_signals has length 1 for no parser
                args["packet_size"] = np.prod(
                    np.array(literal_eval(str(args["shape"])))
                )
            if not out_dtype:
                if len(in_signals) == 1:
                    out_dtype = list(in_signals.values())[0]["ctype"]
                else:
                    out_dtype = "uint8_t"

            # if logger, group signals in different data structs depending on
            # storage type
            tick_table_sigs = {}
            custom_tables = {}  # signals to be logged in their own tables
            msgpack_sigs = []  # signals to be wrapped in msgpack
            extra_cols = 0

            if out_signal["args"]["type"] == "disk":
                # TODO this validation and logic should be moved to driver

                # TODO figure out buffer sizing
                schema_size = 0
                for sig in in_signals:
                    args = in_signals[sig]

                    # validate history is at least FLUSH length
                    sql_logger_flush = config["config"]["sql_logger_flush"]
                    if args["history"] < sql_logger_flush:
                        print(
                            "Warning: logger in signal history must be "
                            "at least sql_logger_flush "
                        )
                        args["history"] = sql_logger_flush

                    # format and validate `log` keyword args
                    log = args.get("log")
                    if isinstance(log, bool):
                        if log:
                            args["log"] = {
                                "enable": True,
                                "type": "auto",
                                "table": "tick",
                                "num_cols": 1,
                            }
                        else:
                            continue
                    elif isinstance(log, dict):
                        if log.get("enable", True):
                            if "type" not in log:
                                log["type"] = "auto"
                            if "table" not in log:
                                log["table"] = "tick"
                            log["num_cols"] = 1
                            log["enable"] = True
                        else:
                            continue
                    else:
                        raise ValueError(
                            "`log` keyword must have type bool or dict"
                        )
                    log = args["log"]
                    if log["table"] == "tick":
                        in_signals[sig] = args
                        tick_table_sigs[sig] = args
                    else:
                        if log["table"] == "signal":
                            table_name = sig
                        else:
                            table_name = log["table"]
                        in_signals[sig] = args
                        if custom_tables.get(table_name):
                            custom_tables[table_name][sig] = args
                        else:
                            custom_tables[table_name] = {sig: args}

                    schema_size += args["buf_tot_numel"] * args["bytes"]

                    # automatically determine  optimal signal storage type
                    if log["type"] == "auto":
                        if (
                            isinstance(args["shape"], int)
                            or len(args["shape"]) == 1
                        ):  # if 1D signal
                            if args["shape"] == 1:  # scalar
                                in_signals[sig]["log"]["type"] = "scalar"
                            else:  # vector
                                in_signals[sig]["log"]["type"] = "vector"
                        else:  # shape is matrix
                            in_signals[sig]["log"]["type"] = "msgpack"

                    # assign specified storage
                    if log["type"] == "scalar":
                        pass
                    elif log["type"] == "vector":
                        in_signals[sig]["log"]["num_cols"] = args[
                            "packet_size"
                        ]
                        extra_cols += (
                            args["packet_size"] - 1
                        )  # only count *extra* columns
                    elif log["type"] == "text":
                        # determine number of bytes in one signal
                        # element
                        shape = str(args["shape"])
                        if "16" in shape:
                            numBytes = 2
                        elif "32" in shape:
                            numBytes = 4
                        elif "64" in shape:
                            numBytes = 8
                        else:  # int8
                            numBytes = 1
                        in_signals[sig]["log"]["numBytes"] = numBytes
                    elif log["type"] == "msgpack":
                        msgpack_sigs.append(sig)
                    else:  # store as msgpack
                        print(
                            f"Signal shape for {sig} unsupported. "
                            "Signal must be 1-dimensional array to be "
                            f"stored as {log['storage']}."
                        )
                        print(sig + " will be wrapped in msgpack.")
                        in_signals[sig]["log"]["type"] = "msgpack"
                        msgpack_sigs.append(sig)

                    # store abbreviated dtype for use in colName
                    dt = np.dtype(args["dtype"])
                    args["dtype_short"] = dt.kind + str(dt.itemsize)

                out_signal["schema"] = {
                    "data": {
                        "size": schema_size,
                        "dtype": "uint8",
                    }
                }

                # validate custom signal tables
                for table, sigs in custom_tables.items():
                    if len(sigs) > 1:
                        first = True
                        for sig, arg in sigs.items():
                            if first:
                                packet_size = args["packet_size"]
                                max_packets_per_tick = args[
                                    "max_packets_per_tick"
                                ]
                            else:
                                assert packet_size == args["packet_size"]
                                assert (
                                    max_packets_per_tick
                                    == args["max_packets_per_tick"]
                                )

            logger_num_tables = len(custom_tables)
            if any(tick_table_sigs):
                logger_num_tables += 1

            driver_template_name = f'{out_signal["args"]["type"]}'
            driver_output_name = f"{name}_{driver_template_name}"
            async_sink = name in async_writers_dict.keys()
            async_writer_name = async_writers_dict.get(name)
            has_in_signal = len(list(in_signals)) == 1
            sink_template_kwargs = {
                "name": name,  # TODO set name properly for async, etc.
                "sink_num": sink_names.index(name),
                "config": config,
                "has_parser": has_parser,
                "async": async_sink,
                "async_writer_name": async_writer_name,
                "async_writer_num": (
                    async_writer_names.index(async_writer_name)
                    if async_sink
                    else None
                ),
                "in_signals": in_signals,
                # TODO use OrderedDict w/ jinja:
                # https://stackoverflow.com/questions/33742530/how-can-i-print-a-jinja-dict-in-a-deterministic-order
                "in_sig_keys": list(in_signals),
                "has_in_signal": has_in_signal,
                "in_signal_name": (
                    list(in_signals)[0] if has_in_signal else None
                ),
                "in_signal_type": (
                    in_sig_types[list(in_signals)[0]]
                    if has_in_signal
                    else None
                ),
                "in_sig_nums": in_sig_nums,
                "out_sig_name": module_val["out"]["name"],
                "out_signal": out_signal,
                "out_signal_size": out_signal["schema"]["data"]["size"]
                if "schema" in out_signal
                else 1,
                "num_sem_sigs": num_sem_sigs,
                "in_sig_sems": in_sig_sems,
                "sig_types": in_sig_types,  # TODO remove
                "out_dtype": out_dtype,
                "buf_vars_len": BUF_VARS_LEN,
                "source_outputs": list(source_outputs),
                "history_pad_length": HISTORY_DEFAULT,
                "platform_system": platform_system,
                # TODO add clear documentation on how to set this and check max
                "async_buf_len": None
                if (not async_sink)
                else max([x["history"] for x in in_signals.values()]),
                # logger-specific:
                "tick_view_extra_cols": extra_cols,
                "tick_table": tick_table_sigs,
                "custom_table_names": list(custom_tables.keys()),
                "custom_table_sigs": {
                    table: [sig for sig, args in sigs.items()]
                    for table, sigs in custom_tables.items()
                },
                "custom_tables": custom_tables,
                "msgpack_sigs": msgpack_sigs,
                "logger_num_tables": logger_num_tables,
            }

            parser_code = ""
            if has_parser:
                if module_val["parser"] is True:
                    module_val["parser"] = name + "_parser"
                with open(
                    __find_in_path(
                        paths["modules"],
                        [
                            f"{module_val['parser']}{ext}"
                            for ext in in_extensions
                        ],
                    ),
                    "r",
                ) as f:
                    parser_code = f.read()
                    parser_code = parser_code.replace("\n", "\n  ")
                    parser_code = jinja2.Template(parser_code)
                    parser_code = parser_code.render(**sink_template_kwargs)

            construct_code = ""
            if "constructor" in module_val and module_val["constructor"]:
                if module_val["constructor"] is True:
                    module_val["constructor"] = name + "_constructor"
                with open(
                    __find_in_path(
                        paths["modules"],
                        [
                            f"{module_val['constructor']}{ext}"
                            for ext in in_extensions
                        ],
                    ),
                    "r",
                ) as f:
                    construct_code = f.read()
                    construct_code = jinja2.Template(construct_code)
                    construct_code = construct_code.render(
                        **sink_template_kwargs
                    )

            destruct_code = ""
            if "destructor" in module_val and module_val["destructor"]:
                if module_val["destructor"] is True:
                    module_val["destructor"] = name + "_destructor"
                with open(
                    __find_in_path(
                        paths["modules"],
                        [
                            f"{module_val['destructor']}{ext}"
                            for ext in in_extensions
                        ],
                    ),
                    "r",
                ) as f:
                    destruct_code = f.read()
                    destruct_code = destruct_code.replace("\n", "\n  ")
                    destruct_code = jinja2.Template(destruct_code)
                    destruct_code = destruct_code.render(
                        **sink_template_kwargs
                    )

            sink_template_kwargs.update(
                {
                    "parser_code": parser_code,
                    "construct_code": construct_code,
                    "destruct_code": destruct_code,
                }
            )

            # parse sink driver
            driver_template_file = f"{driver_template_name}.pyx.j2"
            driver_output_path = os.path.join(
                paths["output"], f"sink_drivers/{driver_output_name}.pyx"
            )
            do_jinja(
                __find_in_path(
                    paths["templates"], f"sink_drivers/{driver_template_file}"
                ),
                driver_output_path,
                **sink_template_kwargs,
            )

            with open(driver_output_path, "r") as f:
                driver_code = f.read()
            driver_code = {
                code.partition("\n")[0].strip(): code.partition("\n")[2]
                for code in filter(
                    None, driver_code.split("# __DRIVER_CODE__")
                )
            }

            # parse sink async writer if async
            if async_sink:
                do_jinja(
                    __find_in_path(paths["templates"], template),
                    os.path.join(
                        paths["output"], async_writer_name + out_extension
                    ),
                    driver_code=driver_code,
                    is_main_process=False,
                    is_writer=True,
                    **sink_template_kwargs,
                )

            # parse sink template
            do_jinja(
                __find_in_path(paths["templates"], template),
                os.path.join(paths["output"], name + out_extension),
                driver_code=(None if async_sink else driver_code),
                is_main_process=True,
                is_writer=(not async_sink),
                **sink_template_kwargs,
            )

        # parse module
        else:
            if module_language == "python":
                print(" - " + name + " (py)")
                template = TEMPLATE_MODULE_PY
                in_extensions = [".pyx.j2", ".pyx", ".py.j2", ".py"]
                out_extension = ".pyx"
            else:
                raise NotImplementedError()
                print(" - " + name + " (c)")
                template = TEMPLATE_MODULE_C
                in_extensions = [".c.j2", ".c"]
                out_extension = ".c"

            # prepare module parameters
            out_sig_dependency_info = {}
            for out_sig in module_val["out"]:
                for tmp_name in runner_names:
                    mod = modules[tmp_name]
                    for in_sig in mod["in"]:
                        if in_sig == out_sig:
                            if out_sig in out_sig_dependency_info:
                                out_sig_dependency_info[out_sig] += 1
                            else:
                                out_sig_dependency_info[out_sig] = 1
            for out_sig in out_sig_dependency_info:
                out_sig_dependency_info[out_sig] = (
                    out_sig_dependency_info[out_sig],
                    sig_sem_dict[out_sig],
                )

            in_sig_sems = []
            default_sig_name = ""
            default_params = None
            for in_sig in module_val["in"]:
                if (in_sig in external_signals) and (
                    signals[in_sig]["args"]["type"] == "default"
                ):
                    default_sig_name = in_sig
                    default_params = signals[in_sig]["schema"]["default"]
                # store the signal name in 0 and location of sem in 1
                in_sig_sems.append((in_sig, sig_sem_dict[in_sig]))

            sig_sems = in_sig_sems.copy()
            for out_sig in module_val["out"]:
                sig_sems.append((out_sig, sig_sem_dict[out_sig]))

            in_signals = {
                x: signals[x] for x in (sigkeys & set(module_val["in"]))
            }
            out_signals = {
                x: signals[x] for x in (sigkeys & set(module_val["out"]))
            }
            in_sig_types = {}
            for sig, args in iter(in_signals.items()):
                dtype = args["dtype"]
                dtype = fix_dtype(dtype)
                in_sig_types[sig] = dtype
            out_sig_types = {}
            for sig, args in iter(out_signals.items()):
                dtype = args["dtype"]
                dtype = fix_dtype(dtype)
                out_sig_types[sig] = dtype

            sig_nums = {
                x: internal_signals.index(x)
                for x in (list(in_signals) + list(out_signals))
            }

            module_val["numba"] = "numba" in module_val and module_val["numba"]
            mod_func_inst = None
            func_inputs = None
            if module_val["numba"]:
                # modify user code

                # create funcs and inputs
                func_name = name
                func_sig = "i8("
                func_sig_types = []
                mod_func_insts = []
                for sig in module_val["in"] + module_val["out"]:
                    dt = np.dtype(signals[sig]["dtype"])
                    dim_str = ",".join(
                        [":"] * (str(signals[sig]["shape"]).count(",") + 1)
                    )
                    func_sig_types.append(
                        "{0}{1}[{2}]".format(dt.kind, dt.itemsize, dim_str)
                    )
                    mod_func_insts.append(
                        "np.zeros({0}, dtype='{1}')".format(
                            signals[sig]["shape"], signals[sig]["dtype"]
                        )
                    )
                func_sig += ",".join(func_sig_types)
                func_sig += ")"
                func_inputs = ",".join(module_val["in"] + module_val["out"])
                mod_func_inst = ",".join(mod_func_insts)

            module_template_kwargs = {
                "name": name,
                "args": module_val,
                "config": config,
                "out_sig_dependency_info": out_sig_dependency_info,
                "in_sig_sems": in_sig_sems,
                "sig_sems": sig_sems,
                "in_signals": in_signals,
                "out_signals": out_signals,
                "sig_nums": sig_nums,
                "num_sem_sigs": num_sem_sigs,
                "default_sig_name": default_sig_name,
                "default_params": default_params,
                "module_num": module_names.index(name),
                "in_sig_types": in_sig_types,
                "out_sig_types": out_sig_types,
                "buf_vars_len": BUF_VARS_LEN,
                "numba": module_val["numba"],
                "numba_mod_name": "numba_" + name,
                "numba_func_name": "numba_" + name,
                "numba_func_inputs": func_inputs,
                "numba_inst_inputs": mod_func_inst,
                "top_level": all(
                    [k in list(source_outputs) for k in list(in_signals)]
                ),
                "history_pad_length": HISTORY_DEFAULT,
                "platform_system": platform_system,
            }

            user_code = ""
            file_path = __find_in_path(
                paths["modules"], [f"{name}{ext}" for ext in in_extensions]
            )
            if not os.path.isfile(file_path):
                sys.exit(f"Error: Module {name} file does not exist.")
            with open(file_path, "r") as f:
                user_code = f.read()
                # if module_language == 'python':
                #   user_code = user_code.replace("def ", "cpdef ")
                user_code = user_code.replace("\n", "\n  ")
                user_code = jinja2.Template(user_code)
                user_code = user_code.render(**module_template_kwargs)

            construct_code = ""
            if "constructor" in module_val and module_val["constructor"]:
                if module_val["constructor"] is True:
                    module_val["constructor"] = name + "_constructor"
                file_path = __find_in_path(
                    paths["modules"],
                    [
                        f"{module_val['constructor']}{ext}"
                        for ext in in_extensions
                    ],
                )
                if not os.path.isfile(file_path):
                    sys.exit(
                        f"Error: Module {name} constructor "
                        "file does not exist."
                    )
                with open(file_path, "r") as f:
                    construct_code = f.read()
                    construct_code = jinja2.Template(construct_code)
                    construct_code = construct_code.render(
                        **module_template_kwargs
                    )

            destruct_code = ""
            if "destructor" in module_val and module_val["destructor"]:
                if module_val["destructor"] is True:
                    module_val["destructor"] = name + "_destructor"
                file_path = __find_in_path(
                    paths["modules"],
                    [
                        f"{module_val['destructor']}{ext}"
                        for ext in in_extensions
                    ],
                )
                if not os.path.isfile(file_path):
                    sys.exit(
                        f"Error: Module {name} destructor"
                        " file does not exist."
                    )
                with open(file_path, "r") as f:
                    destruct_code = f.read()
                    destruct_code = destruct_code.replace("\n", "\n  ")
                    destruct_code = jinja2.Template(destruct_code)
                    destruct_code = destruct_code.render(
                        **module_template_kwargs
                    )

            module_template_kwargs.update(
                {
                    "user_code": user_code,
                    "construct_code": construct_code,
                    "destruct_code": destruct_code,
                }
            )

            if module_val["numba"]:
                do_jinja(
                    __find_in_path(paths["templates"], TEMPLATE_NUMBA),
                    os.path.join(paths["output"], "numba_" + name + ".py"),
                    mod_name="numba_" + name,
                    func_name="numba_" + func_name,
                    func_sig=func_sig,
                    func_inputs=func_inputs,
                    user_code=user_code,
                )
                # compile .so file
                os_env = os.environ.copy()
                os_env["PYTHONPATH"] = get_python_lib()
                __handle_completed_process(
                    subprocess.run(
                        ["python", f"numba_{name}.py"],
                        cwd=paths["output"],
                        env=os_env,
                        capture_output=True,
                    )
                )

            do_jinja(
                __find_in_path(paths["templates"], template),
                os.path.join(paths["output"], name + out_extension),
                **module_template_kwargs,
            )

    # parse Makefile
    py_paths = get_paths()
    py_conf_str = f"{get_config_var('BINDIR')}/python3-config"
    py_link_flags = (
        subprocess.check_output([py_conf_str, "--embed", "--ldflags"])
        .decode("utf-8")
        .strip()
    )

    extra_incl = ""
    if platform_system == "Linux":
        extra_incl = "-lrt"

    do_jinja(
        __find_in_path(paths["templates"], TEMPLATE_MAKEFILE),
        os.path.join(paths["output"], OUTPUT_MAKEFILE),
        module_names=module_names,
        source_names=source_names,
        async_reader_names=async_reader_names,
        sink_names=sink_names,
        async_writer_names=async_writer_names,
        source_types=list(map(lambda x: modules[x]["language"], source_names)),
        extra_incl=extra_incl,
        numpy_incl=np.get_include(),
        py_incl=py_paths["include"],
        py_lib=get_config_var("PY_LDFLAGS"),
        py_link_flags=py_link_flags,
        line=compile_for_line,
        darwin=(platform_system == "Darwin"),
    )

    # parse timer parent
    parport_tick_addr = None
    if "config" in config and "parport_tick_addr" in config["config"]:
        parport_tick_addr = config["config"]["parport_tick_addr"]

    do_jinja(
        __find_in_path(paths["templates"], TEMPLATE_TIMER),
        os.path.join(paths["output"], OUTPUT_TIMER),
        config=config,
        topo_order=child_dep_info["topo"],
        topo_widths=child_dep_info["widths"],
        topo_height=child_dep_info["height"],
        num_cores=affinity_info["num_cores"],
        topo_max_width=child_dep_info["max_width"],
        child_dicts=child_dicts,
        # child names and lengths
        num_child_procs=len(child_names),
        child_names=child_names,
        source_names=source_names,
        num_sources=m_info["num_sources"],
        async_reader_names=async_reader_names,
        num_async_readers=num_async_readers,
        module_names=module_names,
        num_modules=m_info["num_modules"],
        sink_names=sink_names,
        num_sinks=m_info["num_sinks"],
        async_writer_names=async_writer_names,
        num_async_writers=num_async_writers,
        internal_signals={
            x: signals[x] for x in (sigkeys & set(internal_signals))
        },
        num_source_sigs=len(list(source_outputs)),
        source_out_sig_nums={
            x: internal_signals.index(x) for x in list(source_outputs)
        },
        sink_in_sig_nums=sink_in_sig_nums,
        parport_tick_addr=parport_tick_addr,
        platform_system=platform_system,
    )

    # parse constants.h
    do_jinja(
        __find_in_path(paths["templates"], TEMPLATE_CONSTANTS),
        os.path.join(paths["output"], OUTPUT_CONSTANTS),
        config=config,
        num_ticks=config["config"]["num_ticks"],
        tick_len_ns=(config["config"]["tick_len"] % 1000000) * 1000,
        tick_len_s=config["config"]["tick_len"] // 1000000,
        cpu_mask=affinity_info["cpu_mask"],
        timer_mask=affinity_info["timer_mask"],
        source_init_ticks=((config["config"].get("source_init_ticks")) or 100),
        module_init_ticks=((config["config"].get("module_init_ticks")) or 0),
        num_sem_sigs=num_sem_sigs,
        num_sinks=m_info["num_sinks"],
        num_async_readers=num_async_readers,
        num_async_writers=num_async_writers,
        num_internal_sigs=len(internal_signals),
        num_source_sigs=len(list(source_outputs)),
        buf_vars_len=BUF_VARS_LEN,
        history_pad_length=HISTORY_DEFAULT,
    )


def export(paths, confirmed):
    os.mkdir(paths["export"])
    # TODO support list of paths
    if os.path.exists(paths["modules"]):
        shutil.copytree(paths["modules"], paths["export"] + "/modules")
    if os.path.exists(paths["output"]):
        shutil.copytree(paths["output"], paths["export"] + "/out")
