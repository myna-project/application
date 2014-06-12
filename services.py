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
import os
import signal

logger = logging.getLogger(__name__)

class ServiceStatus():
    
    def __init__(self):
        self.name = "NoName"
        self.running = False
        
    def to_json(self):
        dict = {}
        for key, value in self.__dict__.items():
            if value != None:
                dict[key] = value
        return dict
    
    
def read_service_status(config):
    list = []
    status = ServiceStatus()
    status.name = "alert"
    status.running = _get_state(config.read_alert_config())
    list.append(status)

    status = ServiceStatus()
    status.name = "logic"
    status.running = _get_state(config.read_logic_config())
    list.append(status)
    
    status = ServiceStatus()
    status.name = "modbus"
    status.running = _get_state(config.read_daemon_config())
   
    list.append(status)
    
    return list

def update_config_modbus(config):
    _update_config(config.read_daemon_config())
    
def update_config_alert(config):
    _update_config(config.read_alert_config())
    
def update_config_logic(config):
    _update_config(config.read_logic_config())

def _update_config(config):
    logger.debug("Reload configuration of %s", config)

    # read pid file 
    pid = _read_pid(config.pidfile)
    # reload configuration
    # if pid != None:
    #    os.kill(int(pid), signal.SIGHUP)
    
def _get_state(config):
    try:
        pid = _read_pid(config.pidfile)
        if pid != None:
            proc = "/proc/" + pid.strip()
            return os.path.exists(proc)
    except Exception, e:
        pass
    return False
    
def _read_pid(pidfile):
    logger.debug("Read the pid file %s", pidfile)
    
    if os.path.exists(pidfile):
        f = open(pidfile, "r")
        for line in f:
            word = line
        f.close()
        logger.debug("\tFound the pid %s", word)
        return word.strip()
    return None
