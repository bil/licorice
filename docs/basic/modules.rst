*******************************************************************************
Writing Module Processes
*******************************************************************************

In LiCoRICE, modules represent user-defined computational blocks which take
inputs, manipulate them, and set outputs. Users are responsible for defining
the sections of a module in their model YAML config and then must create code
snippet files implementing each section. The term `module` is overloaded here
and encompasses sources, internal modules, and sinks. We will commonly refer
to internal modules as just modules and specify `module processes` where
ambiguous when referring to source, internal modules, and sinks.

For a full syntactic description, please check out the
:ref:`YAML Config Reference <api/yaml_config:yaml configuration reference>`.

===============================================================================
Common Properties
===============================================================================

The scaffold surrounding a module exposes some variables that the user may take advantage of:

============ ======== =========================================================
Name         Type     Description
============ ======== =========================================================
time_tick    uint64_t The current system tick 0-indexed to when all module
                      processes start running (set by timer at tick start)
time_system  double   The current tick's start time as measured by
                      clock_gettime using CLOCK_MONOTONIC. Seconds with
                      nanosecond resolution (set by timer at tick start)
============ ======== =========================================================
