import argparse
import yaml
import os
import template_funcs

# do some argument parsing
arg_parser = argparse.ArgumentParser(description='LiCoRICE config parser.')
arg_parser.add_argument('-c', '--config', type=argparse.FileType('r'), help='YAML config file for experiment')
arg_parser.add_argument('-m', '--model', type=argparse.FileType('r'), help='YAML model file to parse')
arg_parser.add_argument('-g', '--generate', action='store_true', help='generate user code templates')
arg_parser.add_argument('-e', '--export', action='store_true', help='export current project')
arg_parser.add_argument('-Q', '--confirm', action='store_true', help='ask for user confirmation on action')
args = arg_parser.parse_args()

if args.export == True:
  export(args.confirm)
  exit()

args = arg_parser.parse_args()

if args.config == None:
  print "Must specify config file."
  exit()

config = yaml.safe_load(args.config)
model = yaml.safe_load(args.model)

# this assumes that a top level object with three primary mappings is loaded
# the only three mappings should be: config, signals, and modules
# later versions should throw an error if this is not true
# Relevant note: this entire parser is dangerous and does not have any safety checks
#    it will break badly for malformed yaml data
top_level = ['config', 'modules', 'signals']
if (set(top_level) != set(model.keys())):
  print("Invalid config file.")
  exit()

# set some paths
paths = {}
paths['templates'] = os.path.join(config['paths']['licorice'], 'templating/templates')
paths['generator'] = os.path.join(config['paths']['licorice'], 'templating/generators')

paths['modules'] = os.path.join(config['paths']['experiments'], 'modules')
paths['output'] = os.path.join(config['paths']['experiments'], 'run/out')
paths['export'] = os.path.join(config['paths']['experiments'], 'run/export')

paths['tmp_modules'] = os.path.join(config['paths']['experiments'], '.modules')
paths['tmp_output'] = os.path.join(config['paths']['experiments'], 'run/.out')


if args.generate == True:
  template_funcs.generate(paths, model, args.confirm)
else: 
  template_funcs.parse(paths, model, args.confirm)
