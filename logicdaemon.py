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
from mydaemon import start_daemon, BaseAppDaemon
import time
import logic
import os
import signal
import logging

if os.path.isfile('/etc/myna/myna.conf'):
    logic.config.cfgfile = "/etc/myna/myna.conf"
else:
    logic.config.cfgfile = "myna.conf"
    
def sighup(signum, frame):
    logging.getLogger('logic').info("SIGHUP received, reloading configuration")
    logic.config.reload()

signal.signal(signal.SIGHUP, sighup)

class LogicApp(BaseAppDaemon):
        
    def __init__(self):
        BaseAppDaemon.__init__(self)
        # set the pid alert
        self.pidfile_path = logic.config.read_logic_config().pidfile  
    def run(self):
        while True:
            logic.do_logics()
            time.sleep(60)
            
# start the application daemon
start_daemon(LogicApp())
