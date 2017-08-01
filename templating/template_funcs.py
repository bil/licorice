import os, shutil
import jinja2
import sys
from toposort import toposort

# some constants
TEMPLATE_DIR='./templates'
GENERATE_DIR='./generate'
MODULE_DIR='./modules'
OUTPUT_DIR='./out'
EXPORT_DIR='./export'

TMP_MODULE_DIR='./.modules'
TMP_OUTPUT_DIR='./.out'

TEMPLATE_MODULE_C='module_c.j2'
TEMPLATE_MODULE_PY='module_py.j2'
TEMPLATE_LOGGER='logger.j2'
TEMPLATE_SINK_PY='sink.pyx.j2'
TEMPLATE_SINK_C='sink.c.j2'
TEMPLATE_SOURCE_PY='source.pyx.j2'
TEMPLATE_SOURCE_C='source.c.j2'
TEMPLATE_MAKEFILE='Makefile.j2'
TEMPLATE_TIMER='timer.j2'
TEMPLATE_CONSTANTS='constants.j2'

GENERATE_MODULE_PY='user_code_py.j2'

OUTPUT_MAKEFILE='Makefile'
OUTPUT_TIMER='timer.c'
OUTPUT_CONSTANTS='constants.h'

MAX_NUM_CORES = 4

def generate(config):
  print "Generating modules...\n"

  if os.path.exists(MODULE_DIR):
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
    if os.path.exists(TMP_MODULE_DIR):
      shutil.rmtree(TMP_MODULE_DIR) 
    shutil.move(MODULE_DIR, TMP_MODULE_DIR)
    print "Moved " + MODULE_DIR + " to " + TMP_MODULE_DIR
    shutil.rmtree(MODULE_DIR, ignore_errors=True)
    print "Removed old output directory.\n"

  os.mkdir(MODULE_DIR)

  print "Generated modules:"
  modules = config['modules']
  for module_name, module_args in modules.iteritems():
    if module_name in ['logger', 'network']:
      continue
    
    # load user code template
    template_f = open(os.path.join(GENERATE_DIR, GENERATE_MODULE_PY), 'r')
    # setup user code template
    user_code_template = jinja2.Template(template_f.read())
    # write to user code file
    user_code_out_f = open(os.path.join(MODULE_DIR, module_name + '.py'), 'w')
    user_code_out_f.write(user_code_template.render( 
      name=module_name, 
      verbose_comments=config['config']['verbose_comments'],
      in_sig=module_args['in'], 
      out_sig=module_args['out']
    ))
    user_code_out_f.close()
    print " -" + module_name

def parse(config):
  print "Parsing"
  # load yaml config
  signals = config['signals']
  sigkeys = set(signals.keys())
  modules = config['modules']

  # set up output directory
  if os.path.exists(OUTPUT_DIR):
    # while True:
    #   sys.stdout.write("Ok to remove old output directory? ")
    #   choice = raw_input().lower()
    #   if choice == 'y':
    #     break
    #   elif choice == 'n':
    #     print "Could not complete parsing. Backup old output directory if necessary and try again."
    #     exit()
    #   else:
    #     print "Please respond with 'y' or 'n'."
    # print 
    if os.path.exists(TMP_OUTPUT_DIR):
      shutil.rmtree(TMP_OUTPUT_DIR) 
    shutil.move(OUTPUT_DIR, TMP_OUTPUT_DIR)
    print "Moved " + OUTPUT_DIR + " to " + TMP_OUTPUT_DIR
    shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
    print "Removing old output directory.\n"

  shutil.copytree(TEMPLATE_DIR, OUTPUT_DIR, ignore=shutil.ignore_patterns(('*.j2')))
  external_signals = []
  internal_signals = []
  for signal_name, signal_args in signals.iteritems():
    if signal_args.has_key('args'):
      external_signals.append(signal_name)
    else: 
      internal_signals.append(signal_name)

  # process modules
  sem_location = 0
  sem_dict = {}
  num_sem_sigs = 0
  logged_signals = {}

  module_names = []
  source_names = []
  sink_names = []
  source_outputs = {}
  dependency_graph = {}
  in_signals = {}
  out_signals = {}
  line_source_exists = 0
  for module_name, module_args in modules.iteritems():
    if all(map(lambda x: x in external_signals, module_args['in'])):
      source_names.append(module_name)
      for sig in module_args['out']:
        source_outputs[sig] = 0
      for sig in module_args['in']:
        assert signals[sig]['args'].has_key('type')
        in_signals[sig] = signals[sig]['args']['type']
    if all(map(lambda x: x in external_signals, module_args['out'])):
      sink_names.append(module_name)
      for sig in module_args['out']:
        assert signals[sig]['args'].has_key('type')
        out_signals[sig] = signals[sig]['args']['type']
    if all(map(lambda x: x in internal_signals, module_args['in'] + module_args['out'])):
      module_names.append(module_name)

    # create semaphore signal mapping w/ format {'sig_name': ptr_offset}
    for sig_name in module_args['in']:
      if not sem_dict.has_key(sig_name):
        sem_dict[sig_name] = sem_location
        sem_location += 1
    num_sem_sigs = len(sem_dict)

  # process input signals
  print "Inputs: "
  for sig_name, sig_type in in_signals.iteritems():
    print " - " + sig_name + ": " + sig_type 
  print "Outputs: "
  for sig_name, sig_type in out_signals.iteritems():
    print " - " + sig_name + ": " + sig_type 

  all_names = source_names + sink_names + module_names
  assert (len(all_names) == len(set(all_names)))

  print "Modules: "

  for name in all_names:
      # get module info
      module_args = modules[name]
      module_language = module_args['language'] # language must be specified

      # parse source
      if name in source_names:
        print " - " + name + " (source)"
        # load network module template
        if module_language == 'python':
          template = TEMPLATE_SOURCE_PY
          extension = '.pyx'
        else:
          template = TEMPLATE_SOURCE_C
          extension = '.c'
        template_f = open(os.path.join(TEMPLATE_DIR, template), 'r')
        # setup network module template
        module_template = jinja2.Template(template_f.read())
        # write to network module file
        mod_out_f = open(os.path.join(OUTPUT_DIR, name + extension), 'w')
        so_in_sig = { x: signals[x] for x in (sigkeys & set(module_args['in'])) }
        assert len(so_in_sig) == 1
        so_in_sig = so_in_sig[so_in_sig.keys()[0]]
        if not so_in_sig['parser']:
          assert len(out_signals) == 1
        if so_in_sig['args']['type'] == 'line':
          line_source_exists = 1
          so_in_sig['schema'] = {}
          so_in_sig['schema']['data'] = {}
          so_in_sig['schema']['data']['dtype'] = 'uint16'
        mod_out_f.write(module_template.render(
          name=name, 
          config=config, 
          signals=signals, 
          out_signals={x: signals[x] for x in (sigkeys & set(module_args['out']))},
          max_buf_size=3750, # TODO, don't hardcode this
          in_signal=so_in_sig
        ))
        mod_out_f.close()
      
      # parse sink
      elif name in sink_names:
        print " - " + name + " (sink)"
        # load logger module template
        if module_language == 'python':
          template = TEMPLATE_SINK_PY
          extension = '.pyx'
        else:
          template = TEMPLATE_SINK_C
          extension = '.c'
        template_f = open(os.path.join(TEMPLATE_DIR, template), 'r')
        # setup logger module template
        module_template = jinja2.Template(template_f.read())
        # write to logger module file
        mod_out_f = open(os.path.join(OUTPUT_DIR, name + extension), 'w')
 
        module_depends_on = []
        source_depends_on = []
        for in_sig in module_args['in']:
          if in_sig in source_outputs.keys():
            #store the signal name in 0 and location of sem in 1
            source_outputs[in_sig] += 1
            source_depends_on.append((in_sig, sem_dict[in_sig]))
          else:
            module_depends_on.append((in_sig, sem_dict[in_sig]))  
        if (name == 'logger'): # TODO make this more generic
          logged_signals = { sig_name: signals[sig_name] for sig_name in module_args['in'] }
        si_out_sig = {x: signals[x] for x in (sigkeys & set(module_args['out']))}
        assert len(si_out_sig) == 1
        si_out_sig = si_out_sig[si_out_sig.keys()[0]]
        if not si_out_sig['parser']:
          assert len(out_signals) == 1
        mod_out_f.write(module_template.render(
          name=name, 
          config=config, 
          cerebus=False, 
          line=False,
          num_sigs=num_sem_sigs,
          s_dep_on=source_depends_on,
          m_dep_on=module_depends_on,
          logged_signals=logged_signals,
          num_logged_signals=len(logged_signals),
          in_signals={x: signals[x] for x in (sigkeys & set(module_args['in']))},
          out_signal=si_out_sig
        ))
        mod_out_f.close()

      # parse cython module type
      elif module_language == 'python':
        print " - " + name + " (py)"
        # load Python module template 
        template_f = open(os.path.join(TEMPLATE_DIR, TEMPLATE_MODULE_PY), 'r')

        # open user Python module code
        mod_user_f = open(os.path.join(MODULE_DIR, name + '.py'), 'r')

        # setup module template
        module_template = jinja2.Template(template_f.read())
        mod_user_code = mod_user_f.read()
        mod_user_code = mod_user_code.replace("def ", "cpdef ")

        # prepare module parameters
        dependencies = {}
        for out_sig in module_args['out']:
          for tmp_name in all_names:
            mod = modules[tmp_name]
            for in_sig in mod['in']:
              if (in_sig == out_sig):
                child_index = all_names.index(tmp_name)
                parent_index = all_names.index(name)
                if dependencies.has_key(in_sig):
                  dependencies[in_sig] += 1
                else:
                  dependencies[in_sig] = 1
                if dependency_graph.has_key(child_index):
                  if all_names[child_index] not in sink_names: # take this out to include sinks in dependency graph
                    dg_cidx = module_names.index(all_names[child_index])
                    dg_pidx = module_names.index(name)
                    dependency_graph[dg_cidx] = dependency_graph[dg_cidx].union({dg_pidx})
                else: 
                  if all_names[child_index] not in sink_names:
                    dg_cidx = module_names.index(all_names[child_index])
                    dg_pidx = module_names.index(name)
                    dependency_graph[dg_cidx] = {dg_pidx}
        for dependency in dependencies:
          #store num dependencies in 0 and location of sem in 1
          dependencies[dependency] = (dependencies[dependency], sem_dict[dependency])

        depends_on = []
        for in_sig in module_args['in']:
          if in_sig in source_outputs.keys():
            source_outputs[in_sig] += 1
          #store the signal name in 0 and location of sem in 1
          depends_on.append((in_sig, sem_dict[in_sig]))

        special_cerebus = []
        if cerebus:
          special_cerebus.append(['spike_ms_timestamps', 'get_spike_ms_timestamps'])
          special_cerebus.append(['channel_ms_timestamps', 'get_channel_ms_timestamps'])
          special_cerebus.append(['ms_spikes', 'get_ms_spikes'])
          special_cerebus.append(['spike_raster', 'get_spike_raster'])
          special_cerebus.append(['ms_data', 'get_ms_data'])
          special_cerebus.append(['channel_data', 'get_channel_data'])
          special_cerebus.append(['all_channel_data', 'get_all_channel_data'])

        special_line = []
        if line:
          pass # TODO must put in methods for getting line data
        # write to Python module file
        mod_out_f = open(os.path.join(OUTPUT_DIR, name + '.pyx'), 'w')
        mod_out_f.write(module_template.render(
          name=name, 
          args=module_args,
          config=config, 
          user_code=mod_user_code, 
          dependencies=dependencies, 
          depends_on=depends_on,
          out_signals = { x: signals[x] for x in (sigkeys & set(module_args['out'])) },
          in_signals = { x: signals[x] for x in (sigkeys & set(module_args['in'])) },
          special_signals=special_cerebus + special_line,
          num_sigs = num_sem_sigs
        ))
        mod_out_f.close()

      # handle C module type
      elif module_language == 'C':
        raise NotImplementedError()
        print " - " + name + "(C)"

        # load C module template 
        template_f = open(os.path.join(TEMPLATE_DIR, TEMPLATE_MODULE_C), 'r')

        # open user C module code
        mod_user_f = open(os.path.join(MODULE_DIR, name + '.c'), 'r')

        # setup module template
        module_template = jinja2.Template(template_f.read())
        mod_user_code = mod_user_f.read()

        # write to to C module file
        mod_out_f = open(os.path.join(OUTPUT_DIR, name + '.c'), 'w')
        mod_out_f.write(module_template.render(
          name=name, 
          config=config, 
          user_code=mod_user_code
        ))
        mod_out_f.close()

  # parse Makefile
  template_f = open(os.path.join(TEMPLATE_DIR, TEMPLATE_MAKEFILE), 'r')
  module_template = jinja2.Template(template_f.read())
  mod_out_f = open(os.path.join(OUTPUT_DIR, OUTPUT_MAKEFILE), 'w')
  mod_out_f.write(module_template.render(
    child_names=module_names,
    logger_needed=(len(logged_signals)!=0),
    source_names=source_names,
    sink_names=sink_names,
    source_types=map(lambda x: modules[x]['language'], source_names)
  ))
  mod_out_f.close()

  # parse timer parent
  template_f = open(os.path.join(TEMPLATE_DIR, TEMPLATE_TIMER), 'r')
  module_template = jinja2.Template(template_f.read())
  mod_out_f = open(os.path.join(OUTPUT_DIR, OUTPUT_TIMER), 'w')
  topo_children = map(list, list(toposort(dependency_graph)))
  topo_lens = map(len, topo_children) # TODO, maybe give warning if too many children on one core? Replaces MAX_NUM_ROUNDS assertion
  num_cores = 1 if len(topo_lens) == 0 else max(topo_lens)
  num_children = len(module_names)
  assert(num_cores < MAX_NUM_CORES)
  source_sems = map(lambda x: [sem_dict[x], source_outputs[x]] , source_outputs.keys())
  parport_tick_addr = config['config']['parport_tick_addr'] if config['config'].has_key('parport_tick_addr') else None
  print parport_tick_addr
  mod_out_f.write(module_template.render(
    config = config,
    topo_order=topo_children,
    topo_lens=topo_lens,
    topo_height=len(topo_children),
    child_names=module_names, 
    num_cores=num_cores,
    num_children=num_children,
    source_names=source_names,
    num_sources=len(source_names),
    sink_names=sink_names,
    num_sinks=len(sink_names),
    num_sigs=num_sem_sigs,
    source_sems=source_sems,
    internal_signals={ x: signals[x] for x in (sigkeys & set(internal_signals)) },
    parport_tick_addr=parport_tick_addr
  ))
  mod_out_f.close()

  # parse constants.h
  template_f = open(os.path.join(TEMPLATE_DIR, TEMPLATE_CONSTANTS), 'r')
  module_template = jinja2.Template(template_f.read())
  mod_out_f = open(os.path.join(OUTPUT_DIR, OUTPUT_CONSTANTS), 'w')
  mod_out_f.write(module_template.render(
    num_children=num_children,
    line=line_source_exists
  ))
  mod_out_f.close()

  print

def export():
  os.mkdir(EXPORT_DIR)
  if os.path.exists(MODULE_DIR):
      shutil.copytree(MODULE_DIR, EXPORT_DIR + "/modules")
  if os.path.exists(OUTPUT_DIR):
    shutil.copytree(OUTPUT_DIR, EXPORT_DIR + "/out")
