import argparse
import yaml
import os
import template_funcs

# do some argument parsing
arg_parser = argparse.ArgumentParser(description='LiCoRICE config parser.')
arg_parser.add_argument('-m', '--model', type=argparse.FileType('r'), help='YAML model file to parse')
arg_parser.add_argument('-g', '--generate', action='store_true', help='generate user code templates')
arg_parser.add_argument('-e', '--export', action='store_true', help='export current project')
arg_parser.add_argument('-Q', '--confirm', action='store_true', help='ask for user confirmation on action')
args = arg_parser.parse_args()

# set some paths
LICORICE_ROOT = os.environ['LICORICE_ROOT']
RIG_ROOT = os.path.join(LICORICE_ROOT, '..')
paths = {}
paths['templates'] = os.path.join(LICORICE_ROOT, 'templating/templates')
paths['generator'] = os.path.join(LICORICE_ROOT, 'templating/generators')

paths['modules'] = os.path.join(RIG_ROOT, 'modules')
paths['output'] = os.path.join(RIG_ROOT, 'run/out')
paths['export'] = os.path.join(RIG_ROOT, 'run/export')

paths['tmp_modules'] = os.path.join(RIG_ROOT, '.modules')
paths['tmp_output'] = os.path.join(RIG_ROOT, 'run/.out')

if args.export == True:
  template_funcs.export(paths, args.confirm)
  exit()

if args.model == None:
  print("Must specify model file.")
  exit()

model = yaml.safe_load(args.model)

# this assumes that a top level object with three primary mappings is loaded
# the only three mappings should be: config, signals, and modules
# later versions should throw an error if this is not true
# Relevant note: this entire parser is dangerous and does not have any safety checks
#    it will break badly for malformed yaml data
top_level = ['config', 'modules', 'signals']
if (not set(model.keys()).issubset(set(top_level))):
  print("Invalid config file.")
  exit()

if args.generate == True:
  template_funcs.generate(paths, model, args.confirm)
else: 
  template_funcs.parse(paths, model, args.confirm)
