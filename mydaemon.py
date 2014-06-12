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
## First configure the logging
import logging.config
import logging.handlers
import os.path

import time
from daemon import runner
import sys
import lockfile
import os

def _setup_logging():
    if os.path.isfile('/etc/myna/logging.conf'):
        logging.config.fileConfig('/etc/myna/logging.conf')
    else:
        logging.config.fileConfig('loggingdev.conf')

logger = logging.getLogger(__name__)

# setup the logging
_setup_logging()

# Base daemon object 
class BaseAppDaemon():
    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/null'
        self.stderr_path = '/dev/null'
        self.pidfile_path =  '/var/run/myna/daemon.pid'
        self.pidfile_timeout = 5
    def run(self):
        while True:
            self.perform_task()
     
    def perform_task(self):
        logger.info("perform task")
        print "test"
        time.sleep(5)
        
        
def list_logger():
    """Return a tree of tuples representing the logger layout.

    Each tuple looks like ``('logger-name', <Logger>, [...])`` where the
    third element is a list of zero or more child tuples that share the
    same layout.

    """
    root = [logging.root]
    items = list(logging.root.manager.loggerDict.items())  # for Python 2 and 3
    items.sort()
    for name, logger in items:
        root.append(logger)

    return root
        
def start_daemon(app):  
    #---------------------------------------------------------------------------#
    # create pid and lockfile directory if it doesn't exists
    #---------------------------------------------------------------------------#
    pidpath = os.path.dirname(app.pidfile_path)
    if not os.path.exists(pidpath):
        try:
            os.mkdir(pidpath)
        except OSError:
            logger.critical("Path %s doesn't exists or insufficient permissions." % pidpath)
            sys.exit(1)
    
    daemon_runner = runner.DaemonRunner(app)
    daemon_runner.daemon_context.files_preserve = []
    
    ## preserve file descriptor 
    logger_tree = list_logger()
    
    for logger_element in logger_tree:
        if hasattr(logger_element, 'handlers'): 
            for hl in logger_element.handlers:
                if isinstance(hl, logging.FileHandler):
                    daemon_runner.daemon_context.files_preserve.append(hl.stream)
    
    daemon_runner.parse_args()
    try:
        daemon_runner.do_action()
    except lockfile.LockTimeout:
        logger.warning("Already running.")
        sys.exit(1)
    except runner.DaemonRunnerStopFailureError:
        logger.warning("Not running.")
        sys.exit(1)
     
    logger.info("Exiting.")
    sys.exit(0)
