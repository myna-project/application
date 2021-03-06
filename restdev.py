#-------------------------------------------------------------------------------
# Copyright (c) 2014 Proxima Centauri srl <info@proxima-centauri.it>.
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the GNU Public License v3.0
# which accompanies this distribution, and is available at
# http://www.gnu.org/licenses/gpl.html
# 
# Contributors:
#     Proxima Centauri srl <info@proxima-centauri.it> - initial API and implementation
#-------------------------------------------------------------------------------
#!/usr/bin/python
# -*- coding: utf-8 -*-


import logging
import logging.config

# configure the logging system
logging.config.fileConfig('loggingdev.conf')

from bottle import run
import bottle
from rest import *

bottle.debug(True)

# Read the configuration
config.cfgfile = "myna.conf"

# start the application
run(app, host='0.0.0.0', port=8010, reloader=False)
