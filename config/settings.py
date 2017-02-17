# Python Import
# -*- coding: utf-8 -*-
import os
import pytz

from json import loads


# Core Import


# Debug mode ###########################################################
AFTER_DONE = True
BEFORE_DONE = True
DEBUG_RESULT = True
########################################################################

# Core Root Path #######################################################
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
# CREDENTIALS = [
#     ['admin', '1234'],
#     ['root', '4321']
# ]
CREDENTIALS = []
########################################################################

# Local Time ###########################################################
local_tz = pytz.timezone('Asia/Tehran')        # use your local timezone
########################################################################

# Scheduler & CronJob ##################################################
threadpool_executor = 20
processpool_executor = 5
coalesce = False
max_instances = 3
########################################################################

# Installed component ##################################################
installed_component = [
    "main",
    "controler"
]
########################################################################


try:
    from settings_local import *
except ImportError:
    pass
