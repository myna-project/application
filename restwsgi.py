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
import os

# configure the logging system
# logging.config.fileConfig('/etc/myna/logging.conf')

from bottle import route, run, request, abort, static_file, template, default_app
import bottle
from rest import *

# Read the configuration
config.cfgfile = "/etc/myna/myna.conf"

root = os.path.dirname(os.path.abspath(__file__))

APP_ROOT = root
bottle.TEMPLATE_PATH.append(os.path.join(APP_ROOT, 'templates'))

if __name__ == '__main__':
    from flup.server.fcgi import WSGIServer
    WSGIServer(app).run()
