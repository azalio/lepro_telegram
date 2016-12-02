import json
import os
import sys
from logging.handlers import SysLogHandler
import logging


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

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
try:
    syslog = SysLogHandler('/dev/log')
except socket.error:
    syslog = SysLogHandler('/var/run/syslog')
formatter = logging.Formatter(u'%(filename)s[LINE:%(lineno)d] %(message)s')
syslog.setFormatter(formatter)
logger.addHandler(syslog)
