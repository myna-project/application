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
import alert
import time
import alert
import os
import signal
import logging

if os.path.isfile('/etc/myna/myna.conf'):
    alert.config.cfgfile = "/etc/myna/myna.conf"
else:
    alert.config.cfgfile = "myna.conf"
    
def sighup(signum, frame):
    logging.getLogger('alarm').info("SIGHUP received, reloading configuration")
    alert.config.reload()

signal.signal(signal.SIGHUP, sighup)

class AlertApp(BaseAppDaemon):
    
    def __init__(self):
        BaseAppDaemon.__init__(self)
        # set the pid alert
        self.pidfile_path = alert.config.read_alert_config().pidfile  
    def run(self):
        while True:
            alert.perform_check()
            time.sleep(60)

# start the application daemon 
start_daemon(AlertApp())            




