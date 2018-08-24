import os, shutil
import jinja2
import sys
from toposort import toposort
import numpy as np
import psutil
from ast import literal_eval
import subprocess
from sysconfig import get_paths
import warnings
import re

# available path constants
# paths['templates']
# paths['generator']
# paths['modules']
# paths['output']
# paths['export']
# paths['tmp_modules']
# paths['tmp_output']

TEMPLATE_MODULE_C='module.c.j2'
TEMPLATE_MODULE_PY='module.py.j2'
TEMPLATE_LOGGER='logger.j2'
TEMPLATE_SINK_PY='sink.pyx.j2'
TEMPLATE_SINK_C='sink.c.j2'
TEMPLATE_SOURCE_PY='source.pyx.j2'
TEMPLATE_SOURCE_C='source.c.j2'
TEMPLATE_MAKEFILE='Makefile.j2'
TEMPLATE_TIMER='timer.j2'
TEMPLATE_CONSTANTS='constants.j2'
TEMPLATE_NUMBA='numba_pycc.j2'

G_TEMPLATE_MODULE_CODE_PY='module_code_py.j2'
G_TEMPLATE_SOURCE_PARSER_PY='source_parser_py.j2'
G_TEMPLATE_SINK_PARSER_PY='sink_parser_py.j2'
G_TEMPLATE_CONSTRUCTOR_PY='constructor_py.j2'
G_TEMPLATE_DESTRUCTOR_PY='destructor_py.j2'
G_TEMPLATE_MODULE_CODE_C='module_code_c.j2'
G_TEMPLATE_SOURCE_PARSER_C='source_parser_c.j2'
G_TEMPLATE_SINK_PARSER_C='sink_parser_c.j2'
G_TEMPLATE_CONSTRUCTOR_C='constructor_c.j2'
G_TEMPLATE_DESTRUCTOR_C='destructor_c.j2'

OUTPUT_MAKEFILE='Makefile'
OUTPUT_TIMER='timer.c'
OUTPUT_CONSTANTS='constants.h'

BUF_VARS_LEN = 16
HISTORY_PAD_LENGTH = 3

# change dtype to C format
def fix_dtype(dtype):
  if 'int' in dtype:
    return dtype + '_t'
  elif dtype == 'float64' or dtype == 'double':
    return 'double'
  elif dtype == 'float32' or dtype == 'float':
    return 'float'
  elif dtype == 'object':
    return 'void'
  return dtype

# change dtype to msgpack format
def fix_dtype_msgpack(dtype):
  if 'float' in dtype or 'double' in dtype:
    dtype = 'float'
  return dtype

# load, setup, and write template
def do_jinja(template_path, out_path, **data):
  template = jinja2.Template(open(template_path, 'r').read())
  out_f = open(out_path, 'w')
  out_f.write(template.render(data))
  out_f.close()

# generate empty templates for modules, parsers, constructors, and destructors
def generate(paths, config, confirm):
  print("Generating modules...\n")

  if os.path.exists(paths['modules']):
    if confirm:
      while True:
        sys.stdout.write("Ok to remove old module directory? ")
        choice = raw_input().lower()
        if choice == 'y':
          break
        elif choice == 'n':
          print("Could not complete generation. Backup old modules if necessary and try again.")
          exit()
        else:
          print("Please respond with 'y' or 'n'.")
    if os.path.exists(paths['tmp_modules']):
      shutil.rmtree(paths['tmp_modules']) 
    shutil.move(paths['modules'], paths['tmp_modules'])
    print("Moved " + paths['modules'] + " to ") + paths['tmp_modules']
    shutil.rmtree(paths['modules'], ignore_errors=True)
    print("Removed old output directory.\n")

  os.mkdir(paths['modules'])

  print("Generated modules:")
  modules = {}
  if 'modules' in config and config['modules']:
    modules = config['modules']
  external_signals = []
  signals = {}
  if 'signals' in config and config['signals']:
    signals = config['signals']
  external_signals = []
  for signal_name, signal_args in iter(signals.items()):
    if 'args' in signal_args:
      external_signals.append(signal_name)

  for module_name, module_args in iter(modules.items()):
    if all(map(lambda x: x in external_signals, module_args['in'])):
      # source
      print(" - " + module_name + " (source)")

      if module_args['language'] == 'python':
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
      if 'parser' in module_args and module_args['parser']:
        if module_args['parser'] == True:
          module_args['parser'] = module_name + "_parser"
        print("   - " + module_args['parser']  + " (parser)")
        do_jinja( os.path.join(paths['generator'], parse_template), 
                  os.path.join(paths['modules'], module_args['parser'] + extension))

      # generate source constructor template
      if 'constructor' in module_args and module_args['constructor']:
        if module_args['constructor'] == True:
          module_args['constructor'] = module_name + "_constructor"
        print("   - " + module_args['constructor']  + " (constructor)")
        do_jinja( os.path.join(paths['generator'], construct_template), 
                  os.path.join(paths['modules'], module_args['constructor'] + extension))

      # generate source destructor template
      if 'destructor' in module_args and module_args['destructor']:
        if module_args['destructor'] == True:
          module_args['destructor'] = module_name + "_destructor"
        print("   - " + module_args['destructor']  + " (destructor)")
        do_jinja( os.path.join(paths['generator'], destruct_template), 
                  os.path.join(paths['modules'], module_args['destructor'] + extension))

    elif all(map(lambda x: x in external_signals, module_args['out'])): 
      # sink
      print(" - " + module_name + " (sink)")

      if module_args['language'] == 'python':
        parse_template = G_TEMPLATE_SOURCE_PARSER_PY
        construct_template = G_TEMPLATE_CONSTRUCTOR_PY
        destruct_template = G_TEMPLATE_DESTRUCTOR_PY
        extension = ".py"
      else: 
        parse_template = G_TEMPLATE_SOURCE_PARSER_C
        construct_template = G_TEMPLATE_CONSTRUCTOR_C
        destruct_template = G_TEMPLATE_DESTRUCTOR_C
        extension = ".c"

      if 'parser' in module_args and module_args['parser']:
        if module_args['parser'] == True:
          module_args['parser'] = module_name + "_parser"
        print("   - " + module_args['parser']  + " (parser)")
        do_jinja( os.path.join(paths['generator'], parse_template), 
                  os.path.join(paths['modules'], module_args['parser'] + extension))

      if 'constructor' in module_args and module_args['constructor']:
        if module_args['constructor'] == True:
          module_args['constructor'] = module_name + "_constructor"
        print("   - " + module_args['constructor']  + " (constructor)")
        do_jinja( os.path.join(paths['generator'], construct_template), 
                  os.path.join(paths['modules'], module_args['constructor'] + extension))

      if 'destructor' in module_args and module_args['destructor']:
        if module_args['destructor'] == True:
          module_args['destructor'] = module_name + "_destructor"
        print("   - " + module_args['destructor']  + " (destructor)")
        do_jinja( os.path.join(paths['generator'], destruct_template), 
                  os.path.join(paths['modules'], module_args['destructor'] + extension))

    else: 
      # module
      print(" - ") + module_name
      do_jinja( os.path.join(paths['generator'], G_TEMPLATE_MODULE_CODE_PY),
                os.path.join(paths['modules'], module_name + '.py'),
                name=module_name, 
                in_sig=module_args['in'], 
                out_sig=module_args['out'] )

      if 'constructor' in module_args and module_args['constructor']:
        if module_args['constructor'] == True:
          module_args['constructor'] = module_name + "_constructor"
        print("   - " + module_args['constructor']  + " (constructor)")
        do_jinja( os.path.join(paths['generator'], construct_template), 
                  os.path.join(paths['modules'], module_args['constructor'] + extension))


      if 'destructor' in module_args and module_args['destructor']:
        if module_args['destructor'] == True:
          module_args['destructor'] = module_name + "_destructor"
        print("   - " + module_args['destructor']  + " (destructor)")
        do_jinja( os.path.join(paths['generator'], destruct_template), 
                  os.path.join(paths['modules'], module_args['destructor'] + extension))


def parse(paths, config, confirm):
  print("Parsing")
  modules = {}
  if 'modules' in config and config['modules']:
    modules = config['modules']
  external_signals = []
  signals = {}
  if 'signals' in config and config['signals']:
    signals = config['signals']
  external_signals = []

  # set up output directory
  if os.path.exists(paths['output']):
    if confirm:
      while True:
        sys.stdout.write("Ok to remove old output directory? ")
        choice = raw_input().lower()
        if choice == 'y':
          break
        elif choice == 'n':
          print("Could not complete parsing. Backup old output directory if necessary and try again.")
          exit()
        else:
          print("Please respond with 'y' or 'n'.")
      print()
    if os.path.exists(paths['tmp_output']):
      shutil.rmtree(paths['tmp_output']) 
    shutil.move(paths['output'], paths['tmp_output'])
    print("Moved " + paths['output'] + " to " + paths['tmp_output'])
    shutil.rmtree(paths['output'], ignore_errors=True)
    print("Removing old output directory.\n")

  # copy helper files to output path
  shutil.copytree(paths['templates'], paths['output'], ignore=shutil.ignore_patterns(('*.j2')))
  
  # set up signal helper variables
  internal_signals = list(signals or []) # list of numpy signal names
  external_signals = []             # list of external signal names

  for signal_name, signal_args in iter(signals.items()):
    signal_args['sig_shape'] = str(signal_args['shape']).partition('(')[2]
    if signal_args['sig_shape'] == '':
      signal_args['sig_shape'] = str(signal_args['shape']) + ')'

    if not 'history' in signal_args :
      signal_args['history'] = 1
    signal_history = signal_args['history']

    signal_args['sig_shape'] = "({0},".format(signal_history + HISTORY_PAD_LENGTH) + signal_args['sig_shape']
    signal_args['buf_tot_numel'] = np.prod(np.array(literal_eval(str(signal_args['sig_shape']))))
    signal_args['tick_numel'] = np.prod(np.array(literal_eval(str(signal_args['shape']))))
    signal_args['dtype_msgpack'] = fix_dtype_msgpack(signal_args['dtype'])
  for module_name, module_args in iter(modules.items()):
    ext_sig = None
    if 'in' in module_args and isinstance(module_args['in'], dict) and 'name' in module_args['in']:
      ext_sig = module_args['in']

      # need 4 times the average per-tick # of bytes since need double packets_per_tick in the 
      # worst case and two full tick lengths to avoid overlap in wrap. 2 would also likely work, but 4 is very safe
      # TODO, maybe packets_per_tick should default to 1 for some inputs? e.g., default, joystick, parport?
      ext_sig['schema']['buf_tot_numel'] = 4 * int(ext_sig['schema']['packets_per_tick']) * int(ext_sig['schema']['data']['size'])
    elif 'out' in module_args and isinstance(module_args['out'], dict) and 'name' in module_args['out']:
      ext_sig = module_args['out']
    else:
      continue
    external_signals.append(ext_sig['name'])
    signals[ext_sig['name']] = ext_sig

  sigkeys = set(signals)

  # process modules
  sem_location = 0
  sig_sem_dict = {}
  num_sem_sigs = 0

  module_names = [] # list of module names
  source_names = [] # list of source names
  sink_names = []   # list of sink names
  source_outputs = {} 
  dependency_graph = {}
  in_signals = {}
  out_signals = {}
  line_source_exists = 0
  num_threaded_sinks = 0

  all_names = list(modules)
  assert (len(all_names) == len(set(all_names)))

  module = False
  for module_name, module_args in iter(modules.items()):
    if 'in' in module_args and isinstance(module_args['in'], dict) and \
       module_args['in']['name'] in external_signals:
      # source
      source_names.append(module_name)
      for sig in module_args['out']:
        source_outputs[sig] = 0
      in_sig_name = module_args['in']['name']
      assert 'type' in signals[in_sig_name]['args']
      in_signals[in_sig_name] = signals[in_sig_name]['args']['type']
      out_sig_schema_num = 0          
      for sig, args in iter({x: signals[x] for x in (sigkeys & set(module_args['out']))}.items()):
        # TODO, should packets_per_tick be copied over?
        if 'schema' in args:
          out_sig_schema_num += 1
        else:
          args['schema'] = signals[module_args['in']['name']]['schema']
      if out_sig_schema_num > 0:
        assert(out_sig_schema_num == len(list(out_signals))) 
    elif 'out' in module_args and isinstance(module_args['out'], dict) and \
         module_args['out']['name'] in external_signals:
      # sink
      sink_names.append(module_name)
      out_sig_name = module_args['out']['name']
      assert 'type' in signals[out_sig_name]['args']
      out_signals[out_sig_name] = signals[out_sig_name]['args']['type'] 
      if out_signals[out_sig_name] in ['line', 'disk']:
        num_threaded_sinks += 1
    else:
      # module
      if not 'in' in module_args or not module_args['in']:
        module_args['in'] = []
      if not 'out' in module_args or not module_args['out']:
        module_args['out'] = []
      if not isinstance(module_args['in'], list):
        module_args['in'] = [module_args['in']]
      if not isinstance(module_args['out'], list):
        module_args['out'] = [module_args['out']]
      module_names.append(module_name)

  # create semaphore signal mapping w/ format {'sig_name': ptr_offset}
  for sig_name in internal_signals:
    if sig_name not in list(source_outputs) and not sig_name in sig_sem_dict:
      sig_sem_dict[sig_name] = sem_location
      sem_location += 1
  num_sem_sigs = len(sig_sem_dict)

  # create signal dependency graph
  for idx, name in enumerate(module_names):
    args = modules[name]
    deps = set()
    for in_sig in args['in']:
      for dep_idx, dep_name in enumerate(module_names):
        dep_args = modules[dep_name]
        for out_sig in dep_args['out']:
          if (in_sig == out_sig):
            deps = deps.union({dep_idx})
    dependency_graph[idx] = deps

  assert(set(all_names) == set(source_names + module_names + sink_names))
  non_source_names = sink_names + module_names
  topo_children = list(map(list, list(toposort(dependency_graph))))
  topo_widths = list(map(len, topo_children)) # TODO, maybe give warning if too many children on one core? Replaces MAX_NUM_ROUNDS assertion
  topo_height = len(topo_children)
  topo_max_width = 0 if len(topo_widths) == 0 else max(topo_widths)
  num_cores_used = 1 + len(source_names) + topo_max_width + len(sink_names) + num_threaded_sinks # TODO put threaded sink threads on cores w modules
  num_cores_avail = psutil.cpu_count()

  if num_cores_used > num_cores_avail :
    warnings.warn('WARNING: Computer running LiCoRICE may not have sufficient cores to execute this model successfully.')

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
      module_language = module_args['language'] # language must be specified

      # parse source
      if name in source_names:
        print(" - " + name + " (source)")

        if module_language == 'python':
          template = TEMPLATE_SOURCE_PY
          in_extension = '.py'
          out_extension = '.pyx'
        else:
          template = TEMPLATE_SOURCE_C
          in_extension = '.c'
          out_extension = '.c'
        in_signal = signals[module_args['in']['name']]
        out_signals = {x: signals[x] for x in (sigkeys & set(module_args['out']))}
        out_sig_nums = {x: internal_signals.index(x) for x in list(out_signals)}
        has_parser = 'parser' in module_args and module_args['parser']
        if (not has_parser): assert len(out_signals) == 1 
        default_params = in_signal['schema']['default'] if (in_signal['args']['type'] == 'default') else None

        if in_signal['args']['type'] == 'line':
          print("Line input not supported")
          exit()
          line_source_exists = 1
          in_signal['schema'] = {}
          in_signal['schema']['data'] = {}
          in_signal['schema']['data']['dtype'] = 'uint16'
      
        in_dtype = in_signal['schema']['data']['dtype']
        in_dtype = fix_dtype(in_dtype)
        out_sig_types = {}
        for sig, args in iter(out_signals.items()):
          dtype = args['dtype']
          dtype = fix_dtype(dtype)
          out_sig_types[sig] = dtype
          if not has_parser: assert in_dtype == dtype  # out_signals has length 1 for no parser
          args['tick_numel'] = np.prod(np.array(literal_eval(str(args['shape']))))

        parser_code = ""
        if has_parser:
          if module_args['parser'] == True:
            module_args['parser'] = name + "_parser"
          with open(os.path.join(paths['modules'], module_args['parser'] + in_extension), 'r') as f:
            parser_code = f.read()
            parser_code = parser_code.replace("\n", "\n  ")

        construct_code = ""
        if 'constructor' in module_args and module_args['constructor']:
          if module_args['constructor'] == True:
            module_args['constructor'] = name + "_constructor"
          with open(os.path.join(paths['modules'], module_args['constructor'] + in_extension), 'r') as f:
            construct_code = f.read()

        destruct_code = ""
        if 'destructor' in module_args and module_args['destructor']:
          if module_args['destructor'] == True:
            module_args['destructor'] = name + "_destructor"
          with open(os.path.join(paths['modules'], module_args['destructor'] + in_extension), 'r') as f:
            destruct_code = f.read()
            destruct_code = destruct_code.replace("\n", "\n  ")
        do_jinja( os.path.join(paths['templates'], template), 
                  os.path.join(paths['output'], name + out_extension),
                  name=name, 
                  source_num=source_names.index(name),
                  config=config,
                  has_parser=has_parser,
                  parser_code=parser_code,
                  construct_code=construct_code,
                  destruct_code=destruct_code, 
                  in_sig_name=module_args['in']['name'],
                  in_signal=in_signal,
                  out_signals=out_signals,
                  out_signal_name=(None if (has_parser) else list(out_signals)[0]),
                  out_signal_type=(None if (has_parser) else out_sig_types[list(out_signals)[0]]),
                  out_sig_nums=out_sig_nums,
                  default_params=default_params,
                  num_sem_sigs=num_sem_sigs,
                  in_dtype=in_dtype,
                  sig_types=out_sig_types,
                  buf_vars_len=BUF_VARS_LEN
                )
      
      # parse sink
      elif name in sink_names:
        print(" - " + name + " (sink)")
        if module_language == 'python':
          template = TEMPLATE_SINK_PY
          in_extension = '.py'
          out_extension = '.pyx'
        else:
          template = TEMPLATE_SINK_C
          in_extension = '.c'
          out_extension = '.c'
        in_signals = {}
        if 'in' in module_args:
          in_signals = {x: signals[x] for x in (sigkeys & set(module_args['in']))}
        in_sig_nums = {x: internal_signals.index(x) for x in list(in_signals)}
        out_signal = signals[module_args['out']['name']]
        sig_type = out_signal['args']['type']
        has_parser = 'parser' in module_args and module_args['parser']
        if ((not has_parser) and (out_signal['args']['type'] != 'disk')): assert len(in_signals) == 1 
        # buffer_parser = has_parser and out_signal['args']['type'] != 'vis_pygame'

        module_depends_on = []
        for sig,args in iter(in_signals.items()):
          if sig in list(source_outputs):
            #store the signal name in 0 and location of sem in 1
            source_outputs[sig] += 1
          else:
            module_depends_on.append((sig, sig_sem_dict[sig]))  
          
        out_dtype = None
        if has_parser and out_signal['args']['type'] != 'vis_pygame':
          out_dtype = out_signal['schema']['data']['dtype']
          out_dtype = fix_dtype(out_dtype)
        in_sig_types = {}
        for sig, args in iter(in_signals.items()):
          dtype = args['dtype']
          dtype = fix_dtype(dtype)
          in_sig_types[sig] = dtype
          if not has_parser and out_dtype: assert (out_dtype == dtype) # in_signals has length 1 for no parser
        if not out_dtype:
          out_dtype = "uint8_t"

        parser_code = ""
        if has_parser and (module_args['parser'] == True):
          module_args['parser'] = name + "_parser"
          with open(os.path.join(paths['modules'], module_args['parser'] + in_extension), 'r') as f:
            parser_code = f.read()
            parser_code = parser_code.replace("\n", "\n  ")

        construct_code = ""
        if 'constructor' in module_args and module_args['constructor']:
          if module_args['constructor'] == True:
            module_args['constructor'] = name + "_constructor"
          with open(os.path.join(paths['modules'], module_args['constructor'] + in_extension), 'r') as f:
            construct_code = f.read()

        destruct_code = ""
        if 'destructor' in module_args and module_args['destructor']:
          if module_args['destructor'] == True:
            module_args['destructor'] = name + "_destructor"
          with open(os.path.join(paths['modules'], module_args['destructor'] + in_extension), 'r') as f:
            destruct_code = f.read()
            destruct_code = destruct_code.replace("\n", "\n  ")
            
        do_jinja( os.path.join(paths['templates'], template),
                  os.path.join(paths['output'], name + out_extension),
                  name=name, 
                  non_source_num=non_source_names.index(name),
                  config=config, 
                  has_parser=has_parser,
                  parser_code=parser_code,
                  construct_code=construct_code,
                  destruct_code=destruct_code, 
                  in_signal_name=(None if (has_parser) else list(in_signals)[0]),
                  in_signals=in_signals,
                  in_sig_nums=in_sig_nums,
                  out_sig_name=module_args['out']['name'],
                  out_signal=out_signal,
                  num_sem_sigs=num_sem_sigs,
                  m_dep_on=module_depends_on,
                  sig_types=in_sig_types,
                  out_dtype=out_dtype,
                  sig_type=sig_type,
                  is_vis=(sig_type == 'vis_pygame'),
                  is_single_threaded=((sig_type != 'disk') and (sig_type != 'line')),
                  buf_vars_len=BUF_VARS_LEN,
                  source_outputs=list(source_outputs)
                )

      # parse module
      else:
        if module_language == 'python':
          print(" - " + name + " (py)")
          template = TEMPLATE_MODULE_PY
          in_extension = '.py'
          out_extension = '.pyx'
        else:
          raise NotImplementedError()
          print(" - " + name + " (c)")
          template = TEMPLATE_MODULE_C
          in_extension = '.c'
          out_extension = '.c'

        # prepare module parameters
        dependencies = {}
        for out_sig in module_args['out']:
          for tmp_name in all_names:
            mod = modules[tmp_name]
            for in_sig in mod['in']:
              if (in_sig == out_sig):
                child_index = all_names.index(tmp_name)
                parent_index = all_names.index(name)
                if in_sig in dependencies:
                  dependencies[in_sig] += 1
                else:
                  dependencies[in_sig] = 1
        for dependency in dependencies:
          #store num dependencies in 0 and location of sem in 1
          dependencies[dependency] = (dependencies[dependency], sig_sem_dict[dependency])

        depends_on = []
        default_sig_name = ''
        default_params = None
        for in_sig in module_args['in']:
          if (in_sig in external_signals) and (signals[in_sig]['args']['type'] == 'default'):
            default_sig_name = in_sig
            default_params = signals[in_sig]['schema']['default']
          if in_sig in list(source_outputs):
            source_outputs[in_sig] += 1
          else: 
            # store the signal name in 0 and location of sem in 1
            depends_on.append((in_sig, sig_sem_dict[in_sig]))

        in_signals = {x: signals[x] for x in (sigkeys & set(module_args['in']))}
        out_signals = {x: signals[x] for x in (sigkeys & set(module_args['out']))}
        in_sig_types = {}
        for sig, args in iter(in_signals.items()):
          dtype = args['dtype']
          dtype = fix_dtype(dtype)
          in_sig_types[sig] = dtype
        out_sig_types = {}
        for sig, args in iter(out_signals.items()):
          dtype = args['dtype']
          dtype = fix_dtype(dtype)
          out_sig_types[sig] = dtype

        user_code = ""
        file_path = os.path.join(paths['modules'], name + in_extension)
        if not os.path.isfile(file_path): exit("Error: Module {0} file does not exist.".format(name))
        with open(file_path, 'r') as f:
          user_code = f.read()
          # if module_language == 'python':
          #   user_code = user_code.replace("def ", "cpdef ")
          user_code = user_code.replace("\n", "\n  ")

        construct_code = ""
        if 'constructor' in module_args and module_args['constructor']:
          if module_args['constructor'] == True:
            module_args['constructor'] = name + "_constructor"
          file_path = os.path.join(paths['modules'], module_args['constructor'] + in_extension)
          if not os.path.isfile(file_path): exit("Error: Module {0} constructor file does not exist.".format(name))
          with open(file_path, 'r') as f:
            construct_code = f.read()

        destruct_code = ""
        if 'destructor' in module_args and module_args['destructor']:
          if module_args['destructor'] == True:
            module_args['destructor'] = name + "_destructor"
          file_path = os.path.join(paths['modules'], module_args['destructor'] + in_extension)
          if not os.path.isfile(file_path): exit("Error: Module {0} destructor file does not exist.".format(name))
          with open(file_path, 'r') as f:
            destruct_code = f.read()
            destruct_code = destruct_code.replace("\n", "\n  ")
            
        sig_nums = {x: internal_signals.index(x) for x in (list(in_signals) + list(out_signals))}

        module_args['numba'] = ('numba' in module_args and module_args['numba'])
        mod_func_inst = None
        func_inputs = None
        if module_args['numba']:
          # modify user code

          # create funcs and inputs
          func_name = name
          func_sig = "i8("
          func_sig_types = []
          mod_func_insts = []
          for sig in module_args['in'] + module_args['out']:
            dt = np.dtype(signals[sig]['dtype'])
            dim_str = ','.join([':'] * (str(signals[sig]['shape']).count(',') + 1))
            func_sig_types.append("{0}{1}[{2}]".format(dt.kind, dt.itemsize, dim_str))
            mod_func_insts.append("np.zeros({0}, dtype='{1}')".format(signals[sig]['shape'], signals[sig]['dtype']))
          func_sig += ','.join(func_sig_types) 
          func_sig += ")"
          func_inputs = ','.join(module_args['in'] + module_args['out'])
          mod_func_inst = ','.join(mod_func_insts)
          do_jinja( os.path.join(paths['templates'], TEMPLATE_NUMBA), 
                    os.path.join(paths['output'], 'numba_' + name + '.py'),
                    mod_name='numba_' + name,
                    func_name='numba_' + func_name,
                    func_sig=func_sig,
                    func_inputs=func_inputs,
                    user_code=user_code
                   )
          # compile .so file
          # TODO: change this to subprocess when migrating to python 3.5
          ret = os.system("python {0}/numba_{1}.py".format(paths['output'], name))
          if (ret):
            print("Numba module compilation failed")
            exit()
        do_jinja( os.path.join(paths['templates'], template),
                  os.path.join(paths['output'], name + out_extension),
                  name=name, 
                  args=module_args,
                  config=config, 
                  user_code=user_code,
                  construct_code=construct_code,
                  destruct_code=destruct_code,
                  dependencies=dependencies, 
                  depends_on=depends_on,
                  tick_sem_idx=non_source_names.index(name),
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
                  numba=module_args['numba'],
                  numba_mod_name='numba_' + name,
                  numba_func_name='numba_' + name,
                  numba_func_inputs=func_inputs,
                  numba_inst_inputs=mod_func_inst,
                  top_level=all([k in list(source_outputs) for k in list(in_signals)]),
                  py_maj_ver=sys.version_info[0]

                )

  # parse Makefile 
  py_paths = get_paths()
  py_conf_str = "python-config"
  if sys.version_info.major == 3:
    py_conf_str = "python3.6m-config"
  py_link_flags = subprocess.check_output([py_conf_str,"--ldflags"]).decode("utf-8")
  if sys.version_info.major == 3:
    py_link_flags = re.sub("-L[^\s]+config-[^\s]+", "", py_link_flags) # TODO, make this less sketchy
  assert(x in py_link_flags for x in ["-ldl", "-lutil" "-lm", "-lpthread"])
  do_jinja( os.path.join(paths['templates'], TEMPLATE_MAKEFILE),
            os.path.join(paths['output'], OUTPUT_MAKEFILE),
            module_names=module_names,
            source_names=source_names,
            sink_names=sink_names,
            source_types=list(map(lambda x: modules[x]['language'], source_names)),
            numpy_incl=np.get_include(),
            py_incl=py_paths['include'],
            py_lib=py_paths['stdlib'],
            py_link_flags=py_link_flags
          )

  # parse timer parent
  parport_tick_addr = None
  if 'config' in config and 'parport_tick_addr' in config['config']:
    parport_tick_addr = config['config']['parport_tick_addr']
  non_source_module_check = list(map(lambda x: int(x in module_names), non_source_names))
  do_jinja( os.path.join(paths['templates'], TEMPLATE_TIMER), 
            os.path.join(paths['output'], OUTPUT_TIMER),
            config = config,
            topo_order=topo_children,
            topo_widths=topo_widths,
            topo_height=topo_height,
            num_cores=num_cores_avail,
            topo_max_width=topo_max_width,

            # child names and lengths
            source_names=source_names,
            num_sources=len(source_names),
            module_names=module_names, 
            num_modules=len(module_names),
            sink_names=sink_names,
            num_sinks=len(sink_names),

            internal_signals={ x: signals[x] for x in (sigkeys & set(internal_signals)) },
            num_source_sigs=len(list(source_outputs)),
            source_out_sig_nums={x : internal_signals.index(x) for x in list(source_outputs)},
            parport_tick_addr=parport_tick_addr,
            non_source_module_check=non_source_module_check
          )

  # parse constants.h
  if not 'config' in config:
      config['config'] = {}
  if not 'init_buffer_ticks' in config['config']:
    config['config']['init_buffer_ticks'] = 100
  do_jinja( os.path.join(paths['templates'], TEMPLATE_CONSTANTS),
            os.path.join(paths['output'], OUTPUT_CONSTANTS),
            init_buffer_ticks=(50 if line_source_exists else config['config']['init_buffer_ticks']),
            num_sem_sigs=num_sem_sigs,
            num_non_sources=len(non_source_names),
            num_internal_sigs=len(internal_signals),
            num_source_sigs=len(list(source_outputs)),
            buf_vars_len=BUF_VARS_LEN,
            history_pad_length=HISTORY_PAD_LENGTH
          )


def export(paths, confirm):
  os.mkdir(paths['export'])
  if os.path.exists(paths['modules']):
      shutil.copytree(paths['modules'], paths['export'] + "/modules")
  if os.path.exists(paths['output']):
    shutil.copytree(paths['output'], paths['export'] + "/out")
