import os, shutil
import jinja2
import sys
from toposort import toposort
import numpy as np
import psutil
from ast import literal_eval

# some constants
#paths['templates']='./templates'
#paths['generators']='./generate'
#paths['modules']='../../modules'
#paths['output']='../../run/out'
#paths['export']='./export'
#
#paths['modules']='../../.modules'
#paths['output']='../../run/out'

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
def generate(paths, model, confirm):
  print "Generating modules...\n"

  if os.path.exists(paths['modules']):
    if confirm:
      while True:
        sys.stdout.write("Ok to remove old module directory? ")
        choice = raw_input().lower()
        if choice == 'y':
          break
        elif choice == 'n':
          print "Could not complete generation. Backup old modules if necessary and try again."
          exit()
        else:
          print "Please respond with 'y' or 'n'."
    if os.path.exists(paths['tmp_modules']):
      shutil.rmtree(paths['tmp_modules']) 
    shutil.move(paths['modules'], paths['tmp_modules'])
    print "Moved " + paths['modules'] + " to " + paths['modules']
    shutil.rmtree(paths['modules'], ignore_errors=True)
    print "Removed old output directory.\n"

  os.mkdir(paths['modules'])

  print "Generated modules:"
  modules = model['modules']
  signals = model['signals']
  external_signals = []
  for signal_name, signal_args in signals.iteritems():
    if signal_args.has_key('args'):
      external_signals.append(signal_name)

  for module_name, module_args in modules.iteritems():
    if 'in' in module_args and all(map(lambda x: x in external_signals, module_args['in'])):
      # source
      print " - " + module_name + " (source)"

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
      if module_args.has_key('parser') and module_args['parser']:
        if module_args['parser'] == True:
          module_args['parser'] = module_name + "_parser"
        print "   - " + module_args['parser']  + " (parser)"
        do_jinja( os.path.join(paths['generators'], parse_template), 
                  os.path.join(paths['modules'], module_args['parser'] + extension))

      # generate source constructor template
      if module_args.has_key('constructor') and module_args['constructor']:
        if module_args['constructor'] == True:
          module_args['constructor'] = module_name + "_constructor"
        print "   - " + module_args['constructor']  + " (constructor)"
        do_jinja( os.path.join(paths['generators'], construct_template), 
                  os.path.join(paths['modules'], module_args['constructor'] + extension))

      # generate source destructor template
      if module_args.has_key('destructor') and module_args['destructor']:
        if module_args['destructor'] == True:
          module_args['destructor'] = module_name + "_destructor"
        print "   - " + module_args['destructor']  + " (destructor)"
        do_jinja( os.path.join(paths['generators'], destruct_template), 
                  os.path.join(paths['modules'], module_args['destructor'] + extension))

    elif all(map(lambda x: x in external_signals, module_args['out'])): 
      # sink
      print " - " + module_name + " (sink)"

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

      if module_args.has_key('parser') and module_args['parser']:
        if module_args['parser'] == True:
          module_args['parser'] = module_name + "_parser"
        print "   - " + module_args['parser']  + " (parser)"
        do_jinja( os.path.join(paths['generators'], parse_template), 
                  os.path.join(paths['modules'], module_args['parser'] + extension))

      if module_args.has_key('constructor') and module_args['constructor']:
        if module_args['constructor'] == True:
          module_args['constructor'] = module_name + "_constructor"
        print "   - " + module_args['constructor']  + " (constructor)"
        do_jinja( os.path.join(paths['generators'], construct_template), 
                  os.path.join(paths['modules'], module_args['constructor'] + extension))

      if module_args.has_key('destructor') and module_args['destructor']:
        if module_args['destructor'] == True:
          module_args['destructor'] = module_name + "_destructor"
        print "   - " + module_args['destructor']  + " (destructor)"
        do_jinja( os.path.join(paths['generators'], destruct_template), 
                  os.path.join(paths['modules'], module_args['destructor'] + extension))

    else: 
      # module
      print " - " + module_name
      do_jinja( os.path.join(paths['generators'], G_TEMPLATE_MODULE_CODE_PY),
                os.path.join(paths['modules'], module_name + '.py'),
                name=module_name, 
                verbose_comments=model['config']['verbose_comments'],
                in_sig=module_args['in'], 
                out_sig=module_args['out'] )

      if module_args.has_key('constructor') and module_args['constructor']:
        if module_args['constructor'] == True:
          module_args['constructor'] = module_name + "_constructor"
        print "   - " + module_args['constructor']  + " (constructor)"
        do_jinja( os.path.join(paths['generators'], construct_template), 
                  os.path.join(paths['modules'], module_args['constructor'] + extension))


      if module_args.has_key('destructor') and module_args['destructor']:
        if module_args['destructor'] == True:
          module_args['destructor'] = module_name + "_destructor"
        print "   - " + module_args['destructor']  + " (destructor)"
        do_jinja( os.path.join(paths['generators'], destruct_template), 
                  os.path.join(paths['modules'], module_args['destructor'] + extension))


def parse(paths, model, confirm):
  print "Parsing"
  # load yaml model
  signals = model['signals']
  sigkeys = set(signals.keys())
  modules = model['modules']

  # set up output directory
  if os.path.exists(paths['output']):
    if confirm:
      while True:
        sys.stdout.write("Ok to remove old output directory? ")
        choice = raw_input().lower()
        if choice == 'y':
          break
        elif choice == 'n':
          print "Could not complete parsing. Backup old output directory if necessary and try again."
          exit()
        else:
          print "Please respond with 'y' or 'n'."
      print 
    if os.path.exists(paths['tmp_output']):
      shutil.rmtree(paths['tmp_output']) 
    shutil.move(paths['output'], paths['tmp_output'])
    print "Moved " + paths['output'] + " to " + paths['tmp_output']
    shutil.rmtree(paths['output'], ignore_errors=True)
    print "Removing old output directory.\n"

  shutil.copytree(paths['templates'], paths['output'], ignore=shutil.ignore_patterns(('*.j2')))
  external_signals = []
  internal_signals = []
  async_signals = []
  sync_signals = []
  for signal_name, signal_args in signals.iteritems():
    if signal_args.has_key('args'):
      if signal_args.has_key('schema'):
        signal_args['schema']['data']['numel'] = np.prod(np.array(literal_eval(str(signal_args['schema']['data']['shape']))))
      external_signals.append(signal_name)
    else: 
      print np.array((signal_args['shape']))
      signal_args['numel'] = np.prod(np.array(literal_eval(str(signal_args['shape']))))
      signal_args['dtype_msgpack'] = fix_dtype_msgpack(signal_args['dtype'])
      internal_signals.append(signal_name)

  # process modules
  sem_location = 0
  sig_sem_dict = {}
  num_sem_sigs = 0

  module_names = []
  source_names = []
  sink_names = []
  source_outputs = {}
  dependency_graph = {}
  in_signals = {}
  out_signals = {}
  line_source_exists = 0
  num_threaded_sinks = 0

  all_names = modules.keys()
  assert (len(all_names) == len(set(all_names)))

  for module_name, module_args in modules.iteritems():
    if 'in' in module_args and all(map(lambda x: x in external_signals, module_args['in'])):
      source_names.append(module_name)
      for sig in module_args['out']:
        source_outputs[sig] = 0
      if isinstance(module_args['in'], list):
        assert len(module_args['in']) == 1
      else: 
        module_args['in'] = [module_args['in']]
      for sig in module_args['in']:
        assert signals[sig]['args'].has_key('type')
        in_signals[sig] = signals[sig]['args']['type']
    elif 'out' in module_args and all(map(lambda x: x in external_signals, module_args['out'])):
      sink_names.append(module_name)
      if isinstance(module_args['out'], list):
        assert len(module_args['out']) == 1
      else: 
        module_args['out'] = [module_args['out']]
      for sig in module_args['out']:
        assert signals[sig]['args'].has_key('type')
        out_signals[sig] = signals[sig]['args']['type'] 
        if out_signals[sig] in ['line', 'disk']:
          num_threaded_sinks += 1
    else:
      module_names.append(module_name)

  # create semaphore signal mapping w/ format {'sig_name': ptr_offset}
  for sig_name in internal_signals:
    if sig_name not in source_outputs.keys() and not sig_sem_dict.has_key(sig_name):
      sig_sem_dict[sig_name] = sem_location
      sem_location += 1
  num_sem_sigs = len(sig_sem_dict)

  for idx, name in enumerate(module_names):
    args = modules[name]
    deps = set()
    if 'in' in args:
      for in_sig in args['in']:
        for dep_idx, dep_name in enumerate(module_names):
          dep_args = modules[dep_name]
          for out_sig in dep_args['out']:
            if (in_sig == out_sig):
              deps = deps.union({dep_idx})
    dependency_graph[idx] = deps

  assert(set(all_names) == set(source_names + module_names + sink_names))
  non_source_names = sink_names + module_names
  print non_source_names
  topo_children = map(list, list(toposort(dependency_graph)))
  topo_widths = map(len, topo_children) # TODO, maybe give warning if too many children on one core? Replaces MAX_NUM_ROUNDS assertion
  topo_height = len(topo_children)
  topo_max_width = 0 if len(topo_widths) == 0 else max(topo_widths)
  num_cores_used = 1 + len(source_names) + topo_max_width + len(sink_names) + num_threaded_sinks # TODO put threaded sink threads on cores w modules
  num_cores_avail = psutil.cpu_count()

  assert(num_cores_used <= num_cores_avail)

  # process external signals
  print "Inputs: "
  for sig_name, sig_type in in_signals.iteritems():
    print " - " + sig_name + ": " + sig_type 
  print "Outputs: "
  for sig_name, sig_type in out_signals.iteritems():
    print " - " + sig_name + ": " + sig_type 
  print "Modules: "

  for name in all_names:
      # get module info
      module_args = modules[name]
      module_language = module_args['language'] # language must be specified

      # parse source
      if name in source_names:
        print " - " + name + " (source)"

        if module_language == 'python':
          template = TEMPLATE_SOURCE_PY
          in_extension = '.py'
          out_extension = '.pyx'
        else:
          template = TEMPLATE_SOURCE_C
          in_extension = '.c'
          out_extension = '.c'
        in_signal = { x: signals[x] for x in (sigkeys & set(module_args['in'])) }
        assert len(in_signal) == 1
        in_signal = in_signal[in_signal.keys()[0]]
        out_signals = {x: signals[x] for x in (sigkeys & set(module_args['out']))}
        out_sig_nums = {x: internal_signals.index(x) for x in out_signals.keys()}
        parser = module_args.has_key('parser') and module_args['parser']
        print module_args
        if (not parser): assert len(out_signals) == 1 
        default_params = in_signal['schema']['default'] if (in_signal['args']['type'] == 'default') else None

        if in_signal['args']['type'] == 'line':
          line_source_exists = 1
          in_signal['schema'] = {}
          in_signal['schema']['data'] = {}
          in_signal['schema']['data']['dtype'] = 'uint16'

        in_dtype = in_signal['schema']['data']['dtype']
        in_dtype = fix_dtype(in_dtype)
        out_sig_types = {}
        for sig, args in out_signals.iteritems():
          dtype = args['dtype']
          dtype = fix_dtype(dtype)
          out_sig_types[sig] = dtype
          if not parser: assert in_dtype == dtype  # out_signals has length 1 for no parser
  
        parser_code = ""
        if parser:
          if module_args['parser'] == True:
            module_args['parser'] = name + "_parser"
          with open(os.path.join(paths['modules'], module_args['parser'] + in_extension), 'r') as f:
            parser_code = f.read()
            parser_code = parser_code.replace("\n", "\n  ")

        construct_code = ""
        if module_args.has_key('constructor') and module_args['constructor']:
          if module_args['constructor'] == True:
            module_args['constructor'] = name + "_constructor"
          with open(os.path.join(paths['modules'], module_args['constructor'] + in_extension), 'r') as f:
            construct_code = f.read()

        destruct_code = ""
        if module_args.has_key('destructor') and module_args['destructor']:
          if module_args['destructor'] == True:
            module_args['destructor'] = name + "_destructor"
          with open(os.path.join(paths['modules'], module_args['destructor'] + in_extension), 'r') as f:
            destruct_code = f.read()
            destruct_code = destruct_code.replace("\n", "\n  ")

        do_jinja( os.path.join(paths['templates'], template), 
                  os.path.join(paths['output'], name + out_extension),
                  name=name, 
                  source_num=source_names.index(name),
                  config=model,
                  parser=parser,
                  parser_code=parser_code,
                  construct_code=construct_code,
                  destruct_code=destruct_code, 
                  in_sig_name=module_args['in'][0],
                  in_signal=in_signal,
                  out_signals=out_signals,
                  out_sig_nums=out_sig_nums,
                  default_params=default_params,
                  num_sem_sigs=num_sem_sigs,
                  in_dtype=in_dtype,
                  sig_types=out_sig_types
                )
      
      # parse sink
      elif name in sink_names:
        print " - " + name + " (sink)"
        if module_language == 'python':
          template = TEMPLATE_SINK_PY
          in_extension = '.py'
          out_extension = '.pyx'
        else:
          template = TEMPLATE_SINK_C
          in_extension = '.c'
          out_extension = '.c'
        in_signals = {x: signals[x] for x in (sigkeys & set(module_args['in']))}
        in_sig_nums = {x: internal_signals.index(x) for x in in_signals.keys()}
        out_signal = {x: signals[x] for x in (sigkeys & set(module_args['out']))}
        assert len(out_signal) == 1
        out_signal = out_signal[out_signal.keys()[0]]
        sig_type = out_signal['args']['type']
        has_parser = module_args.has_key('parser') and module_args['parser']
        if ((not has_parser) and (out_signal['args']['type'] != 'disk')): assert len(in_signals) == 1 
        # buffer_parser = has_parser and out_signal['args']['type'] != 'vis'

        module_depends_on = []
        for sig,args in in_signals.iteritems():
          if sig in source_outputs.keys():
            #store the signal name in 0 and location of sem in 1
            source_outputs[sig] += 1
          else:
            module_depends_on.append((sig, sig_sem_dict[sig]))  
          
        out_dtype = None
        if has_parser and out_signal['args']['type'] != 'vis':
          out_dtype = out_signal['schema']['data']['dtype']
          out_dtype = fix_dtype(out_dtype)
        in_sig_types = {}
        for sig, args in in_signals.iteritems():
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
        if module_args.has_key('constructor') and module_args['constructor']:
          if module_args['constructor'] == True:
            module_args['constructor'] = name + "_constructor"
          with open(os.path.join(paths['modules'], module_args['constructor'] + in_extension), 'r') as f:
            construct_code = f.read()

        destruct_code = ""
        if module_args.has_key('destructor') and module_args['destructor']:
          if module_args['destructor'] == True:
            module_args['destructor'] = name + "_destructor"
          with open(os.path.join(paths['modules'], module_args['destructor'] + in_extension), 'r') as f:
            destruct_code = f.read()
            destruct_code = destruct_code.replace("\n", "\n  ")
            
        do_jinja( os.path.join(paths['templates'], template),
                  os.path.join(paths['output'], name + out_extension),
                  name=name, 
                  non_source_num=non_source_names.index(name),
                  config=model, 
                  has_parser=has_parser,
                  parser_code=parser_code,
                  construct_code=construct_code,
                  destruct_code=destruct_code, 
                  in_signal_name=(None if (has_parser) else in_signals.keys()[0]),
                  in_signals=in_signals,
                  in_sig_nums=in_sig_nums,
                  out_sig_name=module_args['out'][0],
                  out_signal=out_signal,
                  num_sem_sigs=num_sem_sigs,
                  m_dep_on=module_depends_on,
                  sig_types=in_sig_types,
                  out_dtype=out_dtype,
                  sig_type=sig_type,
                  is_vis=(sig_type == 'vis'),
                  is_single_threaded=((sig_type != 'disk') and (sig_type != 'line'))
                )

      # parse module
      else:
        if module_language == 'python':
          print " - " + name + " (py)"
          template = TEMPLATE_MODULE_PY
          in_extension = '.py'
          out_extension = '.pyx'
        else:
          raise NotImplementedError()
          print " - " + name + " (c)"
          template = TEMPLATE_MODULE_C
          in_extension = '.c'
          out_extension = '.c'

        # prepare module parameters
        dependencies = {}
        for out_sig in module_args['out']:
          for tmp_name in all_names:
            mod = modules[tmp_name]
            if 'in' in mod :
              for in_sig in mod['in']:
                if (in_sig == out_sig):
                  child_index = all_names.index(tmp_name)
                  parent_index = all_names.index(name)
                  if dependencies.has_key(in_sig):
                    dependencies[in_sig] += 1
                  else:
                    dependencies[in_sig] = 1
        for dependency in dependencies:
          #store num dependencies in 0 and location of sem in 1
          dependencies[dependency] = (dependencies[dependency], sig_sem_dict[dependency])

        depends_on = []
        default_sig_name = ''
        default_params = None
        if 'in' in module_args :
          for in_sig in module_args['in']:
            if (in_sig in external_signals) and (signals[in_sig]['args']['type'] == 'default'):
              default_sig_name = in_sig
              default_params = signals[in_sig]['schema']['default']
            if in_sig in source_outputs.keys():
              source_outputs[in_sig] += 1
            else: 
              # store the signal name in 0 and location of sem in 1
              depends_on.append((in_sig, sig_sem_dict[in_sig]))

          in_signals = {x: signals[x] for x in (sigkeys & set(module_args['in']))}
        else:
          in_signals = {}
        out_signals = {x: signals[x] for x in (sigkeys & set(module_args['out']))}
        in_sig_types = {}
        for sig, args in in_signals.iteritems():
          dtype = args['dtype']
          dtype = fix_dtype(dtype)
          in_sig_types[sig] = dtype
        out_sig_types = {}
        for sig, args in out_signals.iteritems():
          dtype = args['dtype']
          dtype = fix_dtype(dtype)
          out_sig_types[sig] = dtype

        user_code = ""
        with open(os.path.join(paths['modules'], name + in_extension), 'r') as f:
          user_code = f.read()
          # if module_language == 'python':
          #   user_code = user_code.replace("def ", "cpdef ")
          user_code = user_code.replace("\n", "\n    ")

        construct_code = ""
        if module_args.has_key('constructor') and module_args['constructor']:
          if module_args['constructor'] == True:
            module_args['constructor'] = name + "_constructor"
          with open(os.path.join(paths['modules'], module_args['constructor'] + in_extension), 'r') as f:
            construct_code = f.read()
            # construct_code = construct_code.replace("\n","\n  ")

        destruct_code = ""
        if module_args.has_key('destructor') and module_args['destructor']:
          if module_args['destructor'] == True:
            module_args['destructor'] = name + "_destructor"
          with open(os.path.join(paths['modules'], module_args['destructor'] + in_extension), 'r') as f:
            destruct_code = f.read()
            destruct_code = destruct_code.replace("\n", "\n  ")
            
        sig_nums = {x: internal_signals.index(x) for x in (in_signals.keys() + out_signals.keys())}
        do_jinja( os.path.join(paths['templates'], template),
                  os.path.join(paths['output'], name + out_extension),
                  name=name, 
                  args=module_args,
                  config=model, 
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
                  out_sig_types=out_sig_types
                )

  # parse Makefile
  do_jinja( os.path.join(paths['templates'], TEMPLATE_MAKEFILE),
            os.path.join(paths['output'], OUTPUT_MAKEFILE),
            module_names=module_names,
            source_names=source_names,
            sink_names=sink_names,
            source_types=map(lambda x: modules[x]['language'], source_names),
            numpy_incl=np.get_include()
          )

  # parse timer parent
  parport_tick_addr = model['config']['parport_tick_addr'] if model['config'].has_key('parport_tick_addr') else None
  non_source_module_check = map(lambda x: int(x in module_names), non_source_names)
  do_jinja( os.path.join(paths['templates'], TEMPLATE_TIMER), 
            os.path.join(paths['output'], OUTPUT_TIMER),
            config = model,
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
            num_source_sigs=len(source_outputs.keys()),
            source_out_sig_nums={x : internal_signals.index(x) for x in source_outputs.keys()},
            parport_tick_addr=parport_tick_addr,
            non_source_module_check=non_source_module_check
          )

  # parse constants.h
  do_jinja( os.path.join(paths['templates'], TEMPLATE_CONSTANTS),
            os.path.join(paths['output'], OUTPUT_CONSTANTS),
            init_buffer_ticks=(50 if line_source_exists else 1),
            num_sem_sigs=num_sem_sigs,
            num_non_sources=len(non_source_names),
            num_internal_sigs=len(internal_signals),
            num_source_sigs=len(source_outputs.keys())
          )


def export(confirm):
  os.mkdir(paths['export'])
  if os.path.exists(paths['modules']):
      shutil.copytree(paths['modules'], paths['export'] + "/modules")
  if os.path.exists(paths['output']):
    shutil.copytree(paths['output'], paths['export'] + "/out")
