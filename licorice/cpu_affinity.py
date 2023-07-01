import warnings

import psutil

from licorice.utils import BitMask

# TODO these should be configurable
NUM_SYSTEM_CORES = 1
NUM_TIMER_CORES = 1
NUM_ASYNC_CORES = 1


def determine_cpu_affinity(
    m_info,
    config,
    modules,
    module_names,
    child_dicts,
    runner_dep_info,
    module_dep_info,
):
    """Determine CPU affiniry for processes.

    By default, the system will run on the first NUM_SYSTEM_CORES cores,
    and the timer will run on the subsequent NUM_TIMER_CORES.
    Child processes will run as isolated as possible, but as the number
    of cores is constrained, async processes will run on the same core,
    and eventually all process will share cores.

    Args:
        config (dict): LiCoRICE model config
        modules (dict): LiCoRICE modules section of model config
        child_dicts (list): list of dicts specifying information about all
            child processes for this model

    Returns:
        affinity_info (dict):
    """
    child_names = list(map(lambda c: c["name"], child_dicts))
    num_child_procs = len(child_names)
    runner_names = list(modules)

    num_cores = psutil.cpu_count()
    full_mask = int("1" * num_cores, base=2)
    sys_mask = BitMask(
        config["config"].get("sys_mask", int("1" * NUM_SYSTEM_CORES, base=2))
    )
    # TODO ensure sys_mask is implemented and set by LiCoRICE
    timer_mask = BitMask(
        config["config"].get(
            "timer_mask",
            range(NUM_SYSTEM_CORES, NUM_SYSTEM_CORES + NUM_TIMER_CORES),
        )
    ).int

    # cores that LiCoRICE can run on (including timer)
    cpu_mask = BitMask(
        config["config"].get(
            "lico_mask",
            range(NUM_SYSTEM_CORES, num_cores),
        )
    ).int
    if len(bin(cpu_mask)[2:]) > num_cores:
        warnings.warn(
            "Invalid CPU mask. Ignoring cores above available number."
        )
        cpu_mask = cpu_mask & full_mask

    # cores that LiCoRICE can run on (excluding timer)
    child_cpus = BitMask(
        range(NUM_SYSTEM_CORES + NUM_TIMER_CORES, num_cores)
    ).bit_list

    # use int.bit_count() for python3.10+
    num_lico_cores = bin(cpu_mask).count("1")
    if (
        num_cores_used := (NUM_TIMER_CORES + num_child_procs)
    ) <= num_lico_cores:  # case 1
        # each child (including async procs) can run on their own core
        for i in range(num_child_procs):
            child_dicts[i]["cpu_affinity"] = BitMask([child_cpus[i]]).hex_str

    elif (
        num_cores_used := (
            NUM_TIMER_CORES + m_info["num_runners"] + NUM_ASYNC_CORES
        )
    ) <= num_lico_cores:  # case 2
        # runners still run on their own cores. async processes can be
        # combined onto NUM_ASYNC_CORES
        async_cpus = child_cpus[0:NUM_ASYNC_CORES]
        r_cpu_idx = NUM_ASYNC_CORES  # runner CPU index into child_cpus
        for i in range(num_child_procs):
            d = child_dicts[i]
            if d["async"]:
                d["cpu_affinity"] = BitMask(async_cpus).hex_str
            else:
                d["cpu_affinity"] = BitMask([child_cpus[r_cpu_idx]]).hex_str
                r_cpu_idx += 1

    elif (
        num_cores_used := (
            NUM_TIMER_CORES
            + m_info["num_sources"]
            + m_info["num_sinks"]
            + NUM_ASYNC_CORES
            + module_dep_info["max_width"]
        )
    ) <= num_lico_cores:  # case 3
        # sources and sinks can run on their own cores. async processes are
        # combined onto NUM_ASYNC_CORES cores. modules run stacked in parallel
        async_cpus = child_cpus[0:NUM_ASYNC_CORES]
        io_cpu_idx = NUM_ASYNC_CORES
        module_cpus = child_cpus[
            NUM_ASYNC_CORES + m_info["num_sources"] + m_info["num_sinks"] :
        ]
        for i in range(num_child_procs):
            d = child_dicts[i]
            if d["async"]:
                d["cpu_affinity"] = BitMask(async_cpus).hex_str
            elif d["type"] in ["source", "sink"]:
                d["cpu_affinity"] = BitMask([child_cpus[io_cpu_idx]]).hex_str
                io_cpu_idx += 1
            else:  # module
                assert d["type"] == "module"
                mod_idx = module_names.index(d["name"])

                def get_mod_cpu(m):
                    try:
                        return m.index(mod_idx)
                    except ValueError:
                        return None

                mod_topo_idx = list(
                    filter(
                        lambda x: x is not None,
                        list(map(get_mod_cpu, module_dep_info["topo"])),
                    )
                )[0]
                d["cpu_affinity"] = BitMask(
                    [module_cpus[mod_topo_idx]]
                ).hex_str

    elif (
        num_cores_used := (
            NUM_TIMER_CORES + NUM_ASYNC_CORES + runner_dep_info["max_width"]
        )
    ) <= num_lico_cores:  # case 4
        # runners stacked in parallel. async processes run on NUM_ASYNC_CORES
        # cores
        async_cpus = child_cpus[0:NUM_ASYNC_CORES]
        runner_cpus = child_cpus[NUM_ASYNC_CORES:]
        for i in range(num_child_procs):
            d = child_dicts[i]
            if d["async"]:
                d["cpu_affinity"] = BitMask(async_cpus).hex_str
            else:  # runner
                assert d["type"] in ["source", "sink", "module"]
                r_idx = runner_names.index(d["name"])

                def get_runner_cpu(r):
                    try:
                        return r.index(r_idx)
                    except ValueError:
                        return None

                r_topo_idx = list(
                    filter(
                        lambda x: x is not None,
                        list(map(get_runner_cpu, runner_dep_info["topo"])),
                    )
                )[0]
                d["cpu_affinity"] = BitMask([runner_cpus[r_topo_idx]]).hex_str

    elif (
        num_cores_used := (NUM_TIMER_CORES + runner_dep_info["max_width"])
    ) <= num_lico_cores:  # case 5
        # runners stack in parallel. async proceses run on system cores
        for i in range(num_child_procs):
            d = child_dicts[i]
            if d["async"]:
                d["cpu_affinity"] = sys_mask.hex_str
            else:  # runner
                assert d["type"] in ["source", "sink", "module"]
                r_idx = runner_names.index(d["name"])

                def get_runner_cpu(r):
                    try:
                        return r.index(r_idx)
                    except ValueError:
                        return None

                r_topo_idx = list(
                    filter(
                        lambda x: x is not None,
                        list(map(get_runner_cpu, runner_dep_info["topo"])),
                    )
                )[0]
                d["cpu_affinity"] = BitMask([child_cpus[r_topo_idx]]).hex_str

    else:  # cases 6-8
        # insufficient cores to assign specific cores
        warnings.warn("LiCoRICE model will run with insufficient cores.")
        # TODO could further optimize these
        if num_cores >= 3:  # case 6
            num_cores_used = 2
            # isolate timer and assign everything else to CPU2
            for i in range(num_child_procs):
                d = child_dicts[i]
                d["cpu_affinity"] = BitMask([2]).hex_str
        elif num_cores == 2:  # case 7
            num_cores_used = 1
            # assign everything to non-system core
            for i in range(num_child_procs):
                d = child_dicts[i]
                d["cpu_affinity"] = sys_mask.inverse(num_cores).hex_str
        else:  # case 8
            num_cores_used = 1
            # only one core, everything assigned to CPU0
            timer_mask = BitMask([0]).hex_str
            for i in range(num_child_procs):
                d = child_dicts[i]
                d["cpu_affinity"] = BitMask([0]).hex_str

    # override logic with user-defined cpu affinities
    # TODO document
    for i, name in enumerate(child_names):
        d = child_dicts[i]
        if not d["async"]:
            if cpu_mask := modules[name].get("cpu_mask"):
                d["cpu_affinity"] = BitMask(cpu_mask).hex_str
        elif d["type"] == "async_reader":
            sync_name = name.split("_async_reader")[0]
            if cpu_mask := modules[sync_name]["in"].get(
                "async_reader_cpu_mask"
            ):
                d["cpu_affinity"] = BitMask(cpu_mask).hex_str
        else:
            assert d["type"] == "async_writer"
            sync_name = name.split("_async_writer")[0]
            if cpu_mask := modules[sync_name]["out"].get(
                "async_writer_cpu_mask"
            ):
                d["cpu_affinity"] = BitMask(cpu_mask).hex_str

    return {
        "num_cores": num_cores,
        "num_cores_used": num_cores_used,
        "cpu_mask": cpu_mask,
        "timer_mask": timer_mask,
    }
