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

import modbus_client

class DeviceStatus():
    
    def __init__(self):
        self.unit = None
        self.value = None
        self.id = None
        self.type = None
        
    def to_json(self):
        dict = {}
        for key, value in self.__dict__.items():
            if value != None:
                dict[key] = value
        return dict

## Read the device status 
def get_device_status(device, daemon_config):
    ## open the client
    client = modbus_client.open_client(daemon_config.getGwAddress(), daemon_config.ListenPort)

    # create the device status 
    status = _get_device_status(device, client)       
        
    modbus_client.close_client(client)
    
    return status

## write the device status 
def write_coil(device, daemon_config, value):
    ## open the client
    client = modbus_client.open_client(daemon_config.getGwAddress(), daemon_config.ListenPort)

    # write the coil
    modbus_client.write_coil(client, device.coil, value)       
        
    modbus_client.close_client(client)
    
## Read the device status 
def get_device_status_list(devices, daemon_config):
    ## open the client
    client = modbus_client.open_client(daemon_config.getGwAddress(), daemon_config.ListenPort)
    
    list = []
    
    for device in devices:
        # create the device status 
        status = _get_device_status(device, client)       
        list.append(status)

    # close modbus connection 
    modbus_client.close_client(client)
    
    return list
                
## Read the device status 
def _get_device_status(device, client):
    status = DeviceStatus()
    status.id = device.id    
    status.type = device.type
    
    if device.type == "Temperature":
        status.value = modbus_client.read_register(client, device.register)
        status.unit = "C"

    if device.type == "OnOff":
        status.value = modbus_client.read_coil(client, device.coil)
    return status
