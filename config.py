import json
import os
import sys


mydir = os.path.dirname(__file__)

try:
    with open(mydir + '/config.json') as fh:
        conf = json.load(fh)
except IOError as exp:
    print('Please, create config.json\n{}'.format(exp))
    exit(1)
except ValueError as exp:
    print('Please, write config')
    exit(1)
