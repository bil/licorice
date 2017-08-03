import argparse
import yaml
from template_funcs import *

# do some argument parsing
arg_parser = argparse.ArgumentParser(description='LiCoRICE config parser.')
arg_parser.add_argument('-c', '--config', type=file, help='config file to parse')
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

# this assumes that a top level object with three primary mappings is loaded
# the only three mappings should be: config, signals, and modules
# later versions should throw an error if this is not true
# Relevant note: this entire parser is dangerous and does not have any safety checks
#    it will break badly for malformed yaml data
top_level = ['config', 'modules', 'signals']
if (set(top_level) != set(config.keys())):
  print("Invalid config file.")
  exit()

if args.generate == True:
  generate(config, args.confirm)
else: 
  parse(config, args.confirm)