import copy
import os
import platform
import shutil
import subprocess
import sys
import warnings
from ast import literal_eval
from distutils.sysconfig import get_config_var, get_python_lib
from sysconfig import get_paths

import jinja2
import numpy as np
import psutil
from toposort import toposort

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
TEMPLATE_LOGGER = "logger.j2"
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
HISTORY_PAD_LENGTH = 4999


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


# change dtype to msgpack format
def fix_dtype_msgpack(dtype):
    if dtype in ["float32", "float"]:
        dtype = "float"
    if dtype in ["float64", "double"]:
        dtype = "double"
    return dtype


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

    modules = {}
    if "modules" in config and config["modules"]:
        modules = config["modules"]
    external_signals = []
    signals = {}
    if "signals" in config and config["signals"]:
        signals = config["signals"]
    external_signals = []
    for signal_name, signal_args in iter(signals.items()):
        if "args" in signal_args:
            external_signals.append(signal_name)

    if "logger" in modules:
        print("Logger detected in model. Adding a bufferer module...")
        bufferer = {}
        bufferer["language"] = "python"
        bufferer["in"] = modules["logger"]["in"]
        modules["bufferer"] = bufferer

    for module_name, module_args in iter(modules.items()):
        if module_args.get("in") and all(
            map(lambda x: x in external_signals, module_args["in"])
        ):
            # source
            print(" - " + module_name + " (source)")

            if module_args["language"] == "python":
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
            if "parser" in module_args and module_args["parser"]:
                if module_args["parser"] is True:
                    module_args["parser"] = module_name + "_parser"
                print("   - " + module_args["parser"] + " (parser)")
                do_jinja(
                    __find_in_path(paths["generators"], parse_template),
                    os.path.join(
                        modules_path, module_args["parser"] + extension
                    ),
                )

            # generate source constructor template
            if "constructor" in module_args and module_args["constructor"]:
                if module_args["constructor"] is True:
                    module_args["constructor"] = module_name + "_constructor"
                print("   - " + module_args["constructor"] + " (constructor)")
                do_jinja(
                    __find_in_path(paths["generators"], construct_template),
                    os.path.join(
                        modules_path,
                        module_args["constructor"] + extension,
                    ),
                )

            # generate source destructor template
            if "destructor" in module_args and module_args["destructor"]:
                if module_args["destructor"] is True:
                    module_args["destructor"] = module_name + "_destructor"
                print("   - " + module_args["destructor"] + " (destructor)")
                do_jinja(
                    __find_in_path(paths["generators"], destruct_template),
                    os.path.join(
                        modules_path, module_args["destructor"] + extension
                    ),
                )

        elif module_args.get("out") and all(
            map(lambda x: x in external_signals, module_args["out"])
        ):
            # sink
            print(" - " + module_name + " (sink)")

            if module_args["language"] == "python":
                parse_template = G_TEMPLATE_SOURCE_PARSER_PY
                construct_template = G_TEMPLATE_CONSTRUCTOR_PY
                destruct_template = G_TEMPLATE_DESTRUCTOR_PY
                extension = ".py"
            else:
                parse_template = G_TEMPLATE_SOURCE_PARSER_C
                construct_template = G_TEMPLATE_CONSTRUCTOR_C
                destruct_template = G_TEMPLATE_DESTRUCTOR_C
                extension = ".c"

            if "parser" in module_args and module_args["parser"]:
                if module_args["parser"] is True:
                    module_args["parser"] = module_name + "_parser"
                print("   - " + module_args["parser"] + " (parser)")
                do_jinja(
                    __find_in_path(paths["generators"], parse_template),
                    os.path.join(
                        modules_path, module_args["parser"] + extension
                    ),
                )

            if "constructor" in module_args and module_args["constructor"]:
                if module_args["constructor"] is True:
                    module_args["constructor"] = module_name + "_constructor"
                print("   - " + module_args["constructor"] + " (constructor)")
                do_jinja(
                    __find_in_path(paths["generators"], construct_template),
                    os.path.join(
                        modules_path,
                        module_args["constructor"] + extension,
                    ),
                )

            if "destructor" in module_args and module_args["destructor"]:
                if module_args["destructor"] is True:
                    module_args["destructor"] = module_name + "_destructor"
                print("   - " + module_args["destructor"] + " (destructor)")
                do_jinja(
                    __find_in_path(paths["generators"], destruct_template),
                    os.path.join(
                        modules_path, module_args["destructor"] + extension
                    ),
                )

        else:
            # module
            print(f" - {module_name}")

            if module_args["language"] == "python":
                code_template = G_TEMPLATE_MODULE_CODE_PY
                construct_template = G_TEMPLATE_CONSTRUCTOR_PY
                destruct_template = G_TEMPLATE_DESTRUCTOR_PY
                extension = ".py"
            else:
                code_template = G_TEMPLATE_MODULE_CODE_C
                construct_template = G_TEMPLATE_CONSTRUCTOR_C
                destruct_template = G_TEMPLATE_DESTRUCTOR_C
                extension = ".c"

            do_jinja(
                __find_in_path(paths["generators"], code_template),
                os.path.join(modules_path, module_name + ".py"),
                name=module_name,
                in_sig=module_args.get("in"),
                out_sig=module_args.get("out"),
            )

            if "constructor" in module_args and module_args["constructor"]:
                if module_args["constructor"] is True:
                    module_args["constructor"] = module_name + "_constructor"
                print("   - " + module_args["constructor"] + " (constructor)")
                do_jinja(
                    __find_in_path(paths["generators"], construct_template),
                    os.path.join(
                        modules_path,
                        module_args["constructor"] + extension,
                    ),
                )

            if "destructor" in module_args and module_args["destructor"]:
                if module_args["destructor"] is True:
                    module_args["destructor"] = module_name + "_destructor"
                print("   - " + module_args["destructor"] + " (destructor)")
                do_jinja(
                    __find_in_path(paths["generators"], destruct_template),
                    os.path.join(
                        modules_path, module_args["destructor"] + extension
                    ),
                )


def parse(paths, config, confirmed):
    print("Parsing")

    platform_system = platform.system()

    # save unmodified config to pass to user-space code
    unmodified_config = copy.deepcopy(config)

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
    external_signals = []
    signals = {}
    if "signals" in config and config["signals"]:
        signals = config["signals"]
    external_signals = []

    if "logger" in modules:
        print("Logger detected in model. Adding a bufferer module...")
        bufferer = {}
        bufferer["language"] = "python"
        bufferer["in"] = modules["logger"]["in"]
        modules["bufferer"] = bufferer

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

        if "history" not in signal_args:
            signal_args["history"] = 1
        signal_history = signal_args["history"]

        signal_args["sig_shape"] = (
            f"({signal_history + HISTORY_PAD_LENGTH},"
            f"{signal_args['sig_shape']}"
        )
        signal_args["buf_tot_numel"] = np.prod(
            np.array(literal_eval(str(signal_args["sig_shape"])))
        )
        signal_args["packet_size"] = np.prod(
            np.array(literal_eval(str(signal_args["shape"])))
        )
        signal_args["ctype"] = fix_dtype(signal_args["dtype"])
        signal_args["dtype_msgpack"] = fix_dtype_msgpack(signal_args["dtype"])

        if "max_packets_per_tick" not in signal_args:
            # TODO top-level signals should potentially inherit from source
            signal_args["max_packets_per_tick"] = 1

    for module_name, module_args in iter(modules.items()):
        ext_sig = None
        if (
            "in" in module_args
            and isinstance(module_args["in"], dict)
            and "name" in module_args["in"]
        ):  # source
            ext_sig = module_args["in"]

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
            "out" in module_args
            and isinstance(module_args["out"], dict)
            and "name" in module_args["out"]
        ):  # sink
            ext_sig = module_args["out"]
        else:  # module
            continue
        external_signals.append(ext_sig["name"])
        signals[ext_sig["name"]] = ext_sig

    sigkeys = set(signals)

    # process modules
    sem_location = 0
    sig_sem_dict = {}
    num_sem_sigs = 0

    module_names = []  # list of module names
    source_names = []  # list of source names
    async_readers_dict = {}  # dict of source: async_readers
    sink_names = []  # list of sink names
    source_outputs = {}
    dependency_graph = {}
    in_signals = {}
    out_signals = {}
    num_threaded_sinks = 0

    all_names = list(modules)
    assert len(all_names) == len(set(all_names))

    logger_database_filename = ""
    compile_for_line = False
    for module_name, module_args in iter(modules.items()):

        if (
            "in" in module_args
            and isinstance(module_args["in"], dict)
            and module_args["in"]["name"] in external_signals
        ):
            source_names.append(module_name)
            if module_args["in"].get("async") or False:
                async_readers_dict[module_name] = f"{module_name}_async_reader"
            for sig in module_args["out"]:
                source_outputs[sig] = 0
            in_sig_name = module_args["in"]["name"]
            assert "type" in signals[in_sig_name]["args"]
            in_signals[in_sig_name] = signals[in_sig_name]["args"]["type"]

            out_sig_schema_num = 0
            for sig, args in iter(
                {
                    x: signals[x] for x in (sigkeys & set(module_args["out"]))
                }.items()
            ):
                # TODO, should max_packets_per_tick be copied over?
                if "schema" in args:
                    out_sig_schema_num += 1
                else:
                    args["schema"] = signals[module_args["in"]["name"]][
                        "schema"
                    ]
            if out_sig_schema_num > 0:
                assert out_sig_schema_num == len(list(out_signals))

        elif (
            "out" in module_args
            and isinstance(module_args["out"], dict)
            and module_args["out"]["name"] in external_signals
        ):
            # sink
            sink_names.append(module_name)
            out_sig_name = module_args["out"]["name"]
            assert "type" in signals[out_sig_name]["args"]
            out_signals[out_sig_name] = signals[out_sig_name]["args"]["type"]
            if out_signals[out_sig_name] in ["line", "disk"]:
                num_threaded_sinks += 1
            if out_signals[out_sig_name] in ["disk"]:
                logger_database_filename = signals[out_sig_name]["args"][
                    "save_file"
                ]
            if out_signals[out_sig_name] in ["line"]:
                compile_for_line = True
        else:
            # module
            if "in" not in module_args or not module_args["in"]:
                module_args["in"] = []
            if "out" not in module_args or not module_args["out"]:
                module_args["out"] = []
            if not isinstance(module_args["in"], list):
                module_args["in"] = [module_args["in"]]
            if not isinstance(module_args["out"], list):
                module_args["out"] = [module_args["out"]]
            module_names.append(module_name)

    # create semaphore signal mapping w/ format {'sig_name': ptr_offset}
    for sig_name in internal_signals:
        if (
            sig_name not in list(source_outputs)
            and sig_name not in sig_sem_dict
        ):
            sig_sem_dict[sig_name] = sem_location
            sem_location += 1
    num_sem_sigs = len(sig_sem_dict)

    # create signal dependency graph
    for idx, name in enumerate(module_names):
        args = modules[name]
        deps = set()
        for in_sig in args["in"]:
            for dep_idx, dep_name in enumerate(module_names):
                dep_args = modules[dep_name]
                for out_sig in dep_args["out"]:
                    if in_sig == out_sig:
                        deps = deps.union({dep_idx})
        dependency_graph[idx] = deps

    ################################################
    assert set(all_names) == set(source_names + module_names + sink_names)
    ################################################

    async_reader_names = list(async_readers_dict.values())
    non_source_names = sink_names + module_names
    topo_children = list(map(list, list(toposort(dependency_graph))))
    topo_widths = list(
        map(len, topo_children)
    )  # TODO, maybe give warning if too many children on one core? Replaces
    # MAX_NUM_ROUNDS assertion
    topo_height = len(topo_children)
    topo_max_width = 0 if len(topo_widths) == 0 else max(topo_widths)
    num_cores_used = (
        1
        + len(source_names)
        + topo_max_width
        + len(sink_names)
        + num_threaded_sinks
    )  # TODO put threaded sink threads on cores w modules
    num_cores_avail = psutil.cpu_count()

    if num_cores_used > num_cores_avail:
        warnings.warn(
            "WARNING: Computer running LiCoRICE may not have sufficient cores "
            "to execute this model successfully."
        )

    # print("system input and output signals")
    print("Inputs: ")
    for sig_name, sig_type in iter(in_signals.items()):
        print(" - " + sig_name + ": " + sig_type)
    print("Outputs: ")
    for sig_name, sig_type in iter(out_signals.items()):
        print(" - " + sig_name + ": " + sig_type)

    # parse sources, sinks and modules
    print("Modules: ")
    for name in all_names:
        # get module info
        module_args = modules[name]
        module_language = module_args["language"]  # language must be specified

        # parse source
        if name in source_names:
            print(" - " + name + " (source)")

            if module_language == "python":
                template = TEMPLATE_SOURCE_PY
                in_extension = ".py"
                out_extension = ".pyx"
            else:
                raise NotImplementedError()
                template = TEMPLATE_SOURCE_C
                in_extension = ".c"
                out_extension = ".c"
            in_signal = signals[module_args["in"]["name"]]
            out_signals = {
                x: signals[x] for x in (sigkeys & set(module_args["out"]))
            }
            out_sig_nums = {
                x: internal_signals.index(x) for x in list(out_signals)
            }
            has_parser = "parser" in module_args and module_args["parser"]

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

            parser_code = ""
            if has_parser:
                if module_args["parser"] is True:
                    module_args["parser"] = name + "_parser"
                with open(
                    __find_in_path(
                        paths["modules"], module_args["parser"] + in_extension
                    ),
                    "r",
                ) as f:
                    parser_code = f.read()
                    parser_code = parser_code.replace("\n", "\n  ")
                    parser_code = jinja2.Template(parser_code)
                    parser_code = parser_code.render(unmodified_config)

            construct_code = ""
            if "constructor" in module_args and module_args["constructor"]:
                if module_args["constructor"] is True:
                    module_args["constructor"] = name + "_constructor"
                with open(
                    __find_in_path(
                        paths["modules"],
                        module_args["constructor"] + in_extension,
                    ),
                    "r",
                ) as f:
                    construct_code = f.read()
                    construct_code = jinja2.Template(construct_code)
                    construct_code = construct_code.render(unmodified_config)

            destruct_code = ""
            if "destructor" in module_args and module_args["destructor"]:
                if module_args["destructor"] is True:
                    module_args["destructor"] = name + "_destructor"
                with open(
                    __find_in_path(
                        paths["modules"],
                        module_args["destructor"] + in_extension,
                    ),
                    "r",
                ) as f:
                    destruct_code = f.read()
                    destruct_code = destruct_code.replace("\n", "\n  ")
                    destruct_code = jinja2.Template(destruct_code)
                    destruct_code = destruct_code.render(unmodified_config)

            driver_template_name = f'{in_signal["args"]["type"]}'
            driver_output_name = f"{name}_{driver_template_name}"
            async_source = name in async_readers_dict.keys()
            async_reader_name = async_readers_dict.get(name)
            source_template_kwargs = {
                "name": name,
                "source_num": source_names.index(name),
                "config": config,
                "has_parser": has_parser,
                "parser_code": parser_code,
                "construct_code": construct_code,
                "destruct_code": destruct_code,
                "async": async_source,
                "async_reader_name": async_reader_name,
                "async_reader_num": (
                    async_reader_names.index(async_reader_name)
                    if async_source
                    else None
                ),
                "in_sig_name": module_args["in"]["name"],
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
                "default_params": default_params,
                "num_sem_sigs": num_sem_sigs,
                "in_dtype": in_dtype,
                "sig_types": out_sig_types,
                "buf_vars_len": BUF_VARS_LEN,
                "py_maj_version": sys.version_info[0],
                "platform_system": platform_system,
            }

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
                in_extension = ".py"
                out_extension = ".pyx"
            else:
                raise NotImplementedError()
                template = TEMPLATE_SINK_C
                in_extension = ".c"
                out_extension = ".c"
            in_signals = {}
            if "in" in module_args:
                in_signals = {
                    x: signals[x] for x in (sigkeys & set(module_args["in"]))
                }
            in_sig_nums = {
                x: internal_signals.index(x) for x in list(in_signals)
            }
            out_signal = signals[module_args["out"]["name"]]
            has_parser = "parser" in module_args and module_args["parser"]
            if (not has_parser) and (out_signal["args"]["type"] != "disk"):
                assert len(in_signals) == 1

            in_sig_sems = []
            for sig, args in iter(in_signals.items()):
                if sig in list(source_outputs):
                    # store the signal name in 0 and location of sem in 1
                    source_outputs[sig] += 1
                else:
                    in_sig_sems.append((sig, sig_sem_dict[sig]))

            out_dtype = None
            if has_parser and out_signal["args"]["type"] != "vis_pygame":
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
            if not out_dtype:
                out_dtype = "uint8_t"

            parser_code = ""
            if has_parser and (module_args["parser"] is True):
                module_args["parser"] = name + "_parser"
                with open(
                    __find_in_path(
                        paths["modules"], module_args["parser"] + in_extension
                    ),
                    "r",
                ) as f:
                    parser_code = f.read()
                    parser_code = parser_code.replace("\n", "\n  ")
                    parser_code = jinja2.Template(parser_code)
                    parser_code = parser_code.render(unmodified_config)

            construct_code = ""
            if "constructor" in module_args and module_args["constructor"]:
                if module_args["constructor"] is True:
                    module_args["constructor"] = name + "_constructor"
                with open(
                    __find_in_path(
                        paths["modules"],
                        module_args["constructor"] + in_extension,
                    ),
                    "r",
                ) as f:
                    construct_code = f.read()
                    construct_code = jinja2.Template(construct_code)
                    construct_code = construct_code.render(unmodified_config)

            destruct_code = ""
            if "destructor" in module_args and module_args["destructor"]:
                if module_args["destructor"] is True:
                    module_args["destructor"] = name + "_destructor"
                with open(
                    __find_in_path(
                        paths["modules"],
                        module_args["destructor"] + in_extension,
                    ),
                    "r",
                ) as f:
                    destruct_code = f.read()
                    destruct_code = destruct_code.replace("\n", "\n  ")
                    destruct_code = jinja2.Template(destruct_code)
                    destruct_code = destruct_code.render(unmodified_config)

            # if logger, group signals in different data structs depending on
            # storage type
            msgpack_sigs = []  # signals to be wrapped in msgpack
            raw_vec_sigs = {}  # map signal to number of columns it will use
            raw_vec_sigs[
                "total"
            ] = 0  # keep track of total number of extra signal columns in db
            raw_text_sigs = (
                {}
            )  # int vector signals to be stored as text in SQL
            # map signal to number of bytes in one element of data
            raw_num_sigs = []  # single number signals

            if out_signal["args"]["type"] == "disk":
                for sig, args in iter(in_signals.items()):

                    # determine whether signal should be logged or not
                    log = False  # if no logging specified
                    if ("log" in args and args["log"] is True) or (
                        "log_storage" in args
                        and (
                            "enable" not in args["log_storage"]
                            or args["log_storage"]["enable"] is True
                        )
                    ):
                        log = True

                    if log is True:
                        # automatically determinae  optimal signal storage type
                        if "log_storage" not in args or (
                            args["log_storage"]["type"] == "auto"
                        ):
                            if (type(args["shape"]) == int) or (
                                len(args["shape"]) == 1
                            ):  # if 1D signal
                                if args["shape"] == 1:
                                    raw_num_sigs.append(sig)
                                else:  # vector
                                    raw_vec_sigs[sig] = args["packet_size"]
                                    raw_vec_sigs["total"] += (
                                        args["packet_size"] - 1
                                    )  # only count *extra* columns
                            else:  # shape is matrix
                                msgpack_sigs.append(sig)

                        # assign specified storage
                        elif ("enable" not in args["log_storage"]) or (
                            args["log_storage"]["enable"] is True
                        ):
                            if args["log_storage"]["type"] == "msgpack":
                                msgpack_sigs.append(sig)
                            elif (type(args["shape"]) == int) or (
                                len(args["shape"]) == 1
                            ):  # if 1D signal
                                if args["log_storage"]["type"] == "vector":
                                    raw_vec_sigs[sig] = args["packet_size"]
                                    raw_vec_sigs["total"] += (
                                        args["packet_size"] - 1
                                    )  # only count *extra* columns
                                elif args["log_storage"]["type"] == "text":
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
                                    raw_text_sigs[sig] = numBytes
                                elif args["log_storage"]["type"] == "raw":
                                    raw_num_sigs.append(sig)
                            else:  # not 1D array, store as msgpack
                                print(
                                    f"Signal shape for {sig} unsupported. "
                                    "Signal must be 1-dimensional array to be "
                                    f"stored as {args['log_storage']}."
                                )
                                print(sig + " will be wrapped in msgpack.")
                                msgpack_sigs.append(sig)

                        # store abbreviated dtype for use in colName
                        dt = np.dtype(args["dtype"])
                        args["dtype_short"] = dt.kind + str(dt.itemsize)

                    else:  # log = False
                        in_signals.pop(sig)
                        in_sig_types.pop(sig)

            driver_template_name = f'{out_signal["args"]["type"]}'
            driver_output_name = f"{name}_{driver_template_name}"
            sink_template_kwargs = {
                "name": name,
                "non_source_num": non_source_names.index(name),
                "config": config,
                "has_parser": has_parser,
                "parser_code": parser_code,
                "construct_code": construct_code,
                "destruct_code": destruct_code,
                "async": module_args["out"].get("async") or False,
                "in_signal_name": None if has_parser else list(in_signals)[0],
                "in_signals": in_signals,
                "msgpack_sigs": msgpack_sigs,
                "raw_vec_sigs": raw_vec_sigs,
                "raw_text_sigs": raw_text_sigs,
                "raw_num_sigs": raw_num_sigs,
                "in_sig_nums": in_sig_nums,
                "out_sig_name": module_args["out"]["name"],
                "out_signal": out_signal,
                "num_sem_sigs": num_sem_sigs,
                "in_sig_sems": in_sig_sems,
                "sig_types": in_sig_types,
                "out_dtype": out_dtype,
                "buf_vars_len": BUF_VARS_LEN,
                "source_outputs": list(source_outputs),
                "history_pad_length": HISTORY_PAD_LENGTH,
                "platform_system": platform_system,
            }

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

            do_jinja(
                __find_in_path(paths["templates"], template),
                os.path.join(paths["output"], name + out_extension),
                driver_code=driver_code,
                **sink_template_kwargs,
            )

        # parse module
        else:
            if module_language == "python":
                print(" - " + name + " (py)")
                template = TEMPLATE_MODULE_PY
                in_extension = ".py"
                out_extension = ".pyx"
            else:
                raise NotImplementedError()
                print(" - " + name + " (c)")
                template = TEMPLATE_MODULE_C
                in_extension = ".c"
                out_extension = ".c"

            # prepare module parameters
            dependencies = {}
            for out_sig in module_args["out"]:
                for tmp_name in all_names:
                    mod = modules[tmp_name]
                    for in_sig in mod["in"]:
                        if in_sig == out_sig:
                            if in_sig in dependencies:
                                dependencies[in_sig] += 1
                            else:
                                dependencies[in_sig] = 1
            for dependency in dependencies:
                # store num dependencies in 0 and location of sem in 1
                dependencies[dependency] = (
                    dependencies[dependency],
                    sig_sem_dict[dependency],
                )

            in_sig_sems = []
            default_sig_name = ""
            default_params = None
            for in_sig in module_args["in"]:
                if (in_sig in external_signals) and (
                    signals[in_sig]["args"]["type"] == "default"
                ):
                    default_sig_name = in_sig
                    default_params = signals[in_sig]["schema"]["default"]
                if in_sig in list(source_outputs):
                    source_outputs[in_sig] += 1
                else:
                    # store the signal name in 0 and location of sem in 1
                    in_sig_sems.append((in_sig, sig_sem_dict[in_sig]))

            sig_sems = in_sig_sems.copy()
            for out_sig in module_args["out"]:
                sig_sems.append((out_sig, sig_sem_dict[out_sig]))

            in_signals = {
                x: signals[x] for x in (sigkeys & set(module_args["in"]))
            }
            out_signals = {
                x: signals[x] for x in (sigkeys & set(module_args["out"]))
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

            user_code = ""
            if not name == "bufferer":
                file_path = __find_in_path(
                    paths["modules"], name + in_extension
                )
                if not os.path.isfile(file_path):
                    sys.exit(f"Error: Module {name} file does not exist.")
                with open(file_path, "r") as f:
                    user_code = f.read()
                    # if module_language == 'python':
                    #   user_code = user_code.replace("def ", "cpdef ")
                    user_code = user_code.replace("\n", "\n  ")
                    user_code = jinja2.Template(user_code)
                    user_code = user_code.render(unmodified_config)

            construct_code = ""
            if "constructor" in module_args and module_args["constructor"]:
                if module_args["constructor"] is True:
                    module_args["constructor"] = name + "_constructor"
                file_path = __find_in_path(
                    paths["modules"], module_args["constructor"] + in_extension
                )
                if not os.path.isfile(file_path):
                    sys.exit(
                        f"Error: Module {name} constructor "
                        "file does not exist."
                    )
                with open(file_path, "r") as f:
                    construct_code = f.read()
                    construct_code = jinja2.Template(construct_code)
                    construct_code = construct_code.render(unmodified_config)

            destruct_code = ""
            if "destructor" in module_args and module_args["destructor"]:
                if module_args["destructor"] is True:
                    module_args["destructor"] = name + "_destructor"
                file_path = __find_in_path(
                    paths["modules"], module_args["destructor"] + in_extension
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
                    destruct_code = destruct_code.render(unmodified_config)

            sig_nums = {
                x: internal_signals.index(x)
                for x in (list(in_signals) + list(out_signals))
            }

            module_args["numba"] = (
                "numba" in module_args and module_args["numba"]
            )
            mod_func_inst = None
            func_inputs = None
            if module_args["numba"]:
                # modify user code

                # create funcs and inputs
                func_name = name
                func_sig = "i8("
                func_sig_types = []
                mod_func_insts = []
                for sig in module_args["in"] + module_args["out"]:
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
                func_inputs = ",".join(module_args["in"] + module_args["out"])
                mod_func_inst = ",".join(mod_func_insts)
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
                name=name,
                args=module_args,
                config=config,
                user_code=user_code,
                construct_code=construct_code,
                destruct_code=destruct_code,
                dependencies=dependencies,
                in_sig_sems=in_sig_sems,
                sig_sems=sig_sems,
                tick_sem_idx=non_source_names.index(name),
                in_signal_name=(
                    None if name != "bufferer" else next(iter(in_signals))
                ),
                in_signals=in_signals,
                out_signals=out_signals,
                sig_nums=sig_nums,
                num_sem_sigs=num_sem_sigs,
                default_sig_name=default_sig_name,
                default_params=default_params,
                module_num=module_names.index(name),
                non_source_num=non_source_names.index(name),
                in_sig_types=in_sig_types,
                out_sig_types=out_sig_types,
                buf_vars_len=BUF_VARS_LEN,
                numba=module_args["numba"],
                numba_mod_name="numba_" + name,
                numba_func_name="numba_" + name,
                numba_func_inputs=func_inputs,
                numba_inst_inputs=mod_func_inst,
                top_level=all(
                    [k in list(source_outputs) for k in list(in_signals)]
                ),
                history_pad_length=HISTORY_PAD_LENGTH,
                platform_system=platform_system,
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
        source_types=list(map(lambda x: modules[x]["language"], source_names)),
        extra_incl=extra_incl,
        numpy_incl=np.get_include(),
        py_incl=py_paths["include"],
        py_lib=get_config_var("PY_LDFLAGS"),
        py_link_flags=py_link_flags,
        line=compile_for_line,
    )

    # parse timer parent
    parport_tick_addr = None
    if "config" in config and "parport_tick_addr" in config["config"]:
        parport_tick_addr = config["config"]["parport_tick_addr"]
    non_source_module_check = list(
        map(lambda x: int(x in module_names), non_source_names)
    )

    do_jinja(
        __find_in_path(paths["templates"], TEMPLATE_TIMER),
        os.path.join(paths["output"], OUTPUT_TIMER),
        config=config,
        topo_order=topo_children,
        topo_widths=topo_widths,
        topo_height=topo_height,
        num_cores=num_cores_avail,
        topo_max_width=topo_max_width,
        # child names and lengths
        source_names=source_names,
        num_sources=len(source_names),
        async_reader_names=async_reader_names,
        num_async_readers=len(async_reader_names),
        module_names=module_names,
        num_modules=len(module_names),
        sink_names=sink_names,
        num_sinks=len(sink_names),
        internal_signals={
            x: signals[x] for x in (sigkeys & set(internal_signals))
        },
        num_source_sigs=len(list(source_outputs)),
        source_out_sig_nums={
            x: internal_signals.index(x) for x in list(source_outputs)
        },
        parport_tick_addr=parport_tick_addr,
        non_source_module_check=non_source_module_check,
        non_source_names=non_source_names,
        num_non_sources=len(module_names) + len(sink_names),
        platform_system=platform_system,
    )

    # parse constants.h
    do_jinja(
        __find_in_path(paths["templates"], TEMPLATE_CONSTANTS),
        os.path.join(paths["output"], OUTPUT_CONSTANTS),
        config=config,
        num_ticks=config["config"]["num_ticks"],
        tick_len_us=config["config"]["tick_len"] % 1000000,
        tick_len_s=config["config"]["tick_len"] // 1000000,
        init_buffer_ticks=((config["config"].get("init_buffer_ticks")) or 100),
        num_sem_sigs=num_sem_sigs,
        num_non_sources=len(non_source_names),
        num_async_readers=len(async_reader_names),
        num_internal_sigs=len(internal_signals),
        num_source_sigs=len(list(source_outputs)),
        buf_vars_len=BUF_VARS_LEN,
        history_pad_length=HISTORY_PAD_LENGTH,
        db_name=logger_database_filename,
    )


def export(paths, confirmed):
    os.mkdir(paths["export"])
    # TODO support list of paths
    if os.path.exists(paths["modules"]):
        shutil.copytree(paths["modules"], paths["export"] + "/modules")
    if os.path.exists(paths["output"]):
        shutil.copytree(paths["output"], paths["export"] + "/out")
