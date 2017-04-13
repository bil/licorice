import os, shutil
import jinja2
import sys

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
TEMPLATE_NETWORK='network.j2'
TEMPLATE_MAKEFILE='Makefile.j2'

GENERATE_MODULE_PY='user_code_py.j2'

OUTPUT_MAKEFILE='Makefile'

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
  modules = config['modules']
  # set up output directory

  if os.path.exists(OUTPUT_DIR):
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
    if os.path.exists(TMP_OUTPUT_DIR):
      shutil.rmtree(TMP_OUTPUT_DIR) 
    shutil.move(OUTPUT_DIR, TMP_OUTPUT_DIR)
    print "Moved " + OUTPUT_DIR + " to " + TMP_OUTPUT_DIR
    shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
    print "Removing old output directory.\n"

  shutil.copytree(TEMPLATE_DIR, OUTPUT_DIR, ignore=shutil.ignore_patterns(('*.j2')))

  # likely need to do something unique with these?
  special_signals = ['logged_signals', 'log_sqlite']

  # process signals
  cerebus = False
  line = False
  if 'cerebus_in' in signals.keys():
    cerebus = True
  if 'line' in signals.keys(): 
    line = True

  # TODO for now, only allow either line or cerebus. one must be specified
  assert cerebus ^ line
  print "Inputs: "
  if cerebus:
    print "- cerebus"
  if line:
    print "- line"

  # process modules

  print
  print "Modules:"
  children = []
  for module_name, module_args in modules.iteritems():
      # get module info
      module_type = module_args['type'] # type must exist

      # handle network special module type
      if module_name == "network":
        print " - network (special)"
        # load network module template
        template_f = open(os.path.join(TEMPLATE_DIR, TEMPLATE_NETWORK), 'r')
        # setup network module template
        module_template = jinja2.Template(template_f.read())
        # write to network module file
        mod_out_f = open(os.path.join(OUTPUT_DIR, 'network.c'), 'w')
        mod_out_f.write(module_template.render(
          name=module_name, 
          config=config, 
          signals=signals, 
          cerebus=cerebus, 
          line=line
        ))
        mod_out_f.close()
      
      # handle logger special moduel type
      elif module_name == "logger":
        print " - logger (special)"
        # load logger module template
        template_f = open(os.path.join(TEMPLATE_DIR, TEMPLATE_LOGGER), 'r')
        # setup logger module template
        module_template = jinja2.Template(template_f.read())
        # write to logger module file
        mod_out_f = open(os.path.join(OUTPUT_DIR, 'logger.c'), 'w')
        mod_out_f.write(module_template.render(
          name=module_name, 
          config=config, 
          cerebus=cerebus, 
          line=line
        ))
        mod_out_f.close()

      # handle cython module type
      elif module_type == 'python':
        print " - " + module_name + " (py)"
        # load Python module template 
        template_f = open(os.path.join(TEMPLATE_DIR, TEMPLATE_MODULE_PY), 'r')

        # open user Python module code
        mod_user_f = open(os.path.join(MODULE_DIR, module_name + '.py'), 'r')

        # setup module template
        module_template = jinja2.Template(template_f.read())
        mod_user_code = mod_user_f.read()
        mod_user_code = mod_user_code.replace("def ", "cpdef ")

        # prepare module parameters
        dependencies = {}
        for out_sig in module_args['out']:
          for name in modules:
            mod = modules[name]
            for in_sig in mod['in']:
              if (in_sig == out_sig):
                if dependencies.has_key(in_sig):
                  dependencies[in_sig] += 1
                else:
                  dependencies[in_sig] = 1

        depends_on = []
        for i in module_args['in']:
          if not signals[i].has_key('special'):
            depends_on.append(i)

        special_cerebus = []
        if cerebus:
          special_cerebus.append(['spike_ms_timestamps', 'get_spike_ms_timestamps'])
          special_cerebus.append(['channel_ms_timestamps', 'get_channel_ms_timestamps'])
          special_cerebus.append(['ms_spikes', 'get_ms_spikes'])
          special_cerebus.append(['spike_raster', 'get_spike_raster'])
          special_cerebus.append(['ms_data', 'get_ms_data'])
          special_cerebus.append(['channel_data', 'get_channel_data'])
          special_cerebus.append(['all_channel_data', 'get_all_channel_data'])

        special_line = {}
        if line:
          pass # TODO must put in methods for getClark S362ting line data

        # write to Python module file
        mod_out_f = open(os.path.join(OUTPUT_DIR, module_name + '.pyx'), 'w')

        mod_out_f.write(module_template.render(
          name=module_name, 
          args=module_args,
          config=config, 
          user_code=mod_user_code, 
          dependencies=dependencies, 
          depends_on=depends_on,
          special_cerebus=special_cerebus
        ))
        mod_out_f.close()
        children.append(module_name)

      # handle C module type
      elif module_type == 'C':
        print " - " + module_name + "(C)"
        # load C module template 
        template_f = open(os.path.join(TEMPLATE_DIR, TEMPLATE_MODULE_C), 'r')

        # open user C module code
        mod_user_f = open(os.path.join(MODULE_DIR, module_name + '.c'), 'r')

        # setup module template
        module_template = jinja2.Template(template_f.read())
        mod_user_code = mod_user_f.read()

        # write to to C module file
        mod_out_f = open(os.path.join(OUTPUT_DIR, module_name + '.c'), 'w')
        mod_out_f.write(module_template.render(
          name=module_name, 
          config=config, 
          user_code=mod_user_code
        ))
        mod_out_f.close()

  # create Makefile

  # load Python module template 
  template_f = open(os.path.join(TEMPLATE_DIR, TEMPLATE_MAKEFILE), 'r')

  # setup module template
  module_template = jinja2.Template(template_f.read())

  # write to to Python module file
  mod_out_f = open(os.path.join(OUTPUT_DIR, OUTPUT_MAKEFILE), 'w')
  mod_out_f.write(module_template.render(children=children))
  mod_out_f.close()

def export():
  os.mkdir(EXPORT_DIR)
  if os.path.exists(MODULE_DIR):
      shutil.copytree(MODULE_DIR, EXPORT_DIR + "/modules")
  if os.path.exists(OUTPUT_DIR):
    shutil.copytree(OUTPUT_DIR, EXPORT_DIR + "/out")
