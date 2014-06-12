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

# Rest interface for myna project 

from bottle import route, run, request, abort, static_file, template, default_app, hook, response, redirect, abort, error
from datetime import date
from exception import RestException, ElementUsedException, LogicTypeAlreadyPresentException
from gzipper import Gzipper

import bottle
import json
import os
import time
import string
import random
import socket
import re
from config import *
from status import DeviceStatus, get_device_status, get_device_status_list, write_coil
from services import read_service_status, update_config_modbus, update_config_logic, update_config_alert

root = os.path.dirname(os.path.abspath(__file__))

logger = logging.getLogger('rest')

def array_to_json(array):
    list = []
    
    for obj in array:
        list.append(obj.to_json())
    return list

# Hook for CORS
@hook('before_request')
def enable_cors():
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'PUT, GET, POST, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

import socket
import fcntl
import struct

# Simple access control system based on ip address  
@hook('before_request')
def simple_ip_checking():
        
    if request.method == "POST" or request.method == "DELETE" or request.method == "PUT":
        ## check allowed/denied ip by reg expression 
        allowed  = config.read_sec_config().allow
        denied  = config.read_sec_config().deny
        logger.debug("filtering ip address for %s allow %s deny %s", request.remote_addr, allowed, denied)
        
        if allowed != "":
            p = re.compile(allowed)
            # check if the ip address is allowed
            if not p.match(request.remote_addr):
                abort(403)
                
        if denied != "":
            p = re.compile(denied)
            # check if the ip address is allowed
            if p.match(request.remote_addr):
                abort(403)
@error(403)
def error403(error):
    response.content_type = 'application/json'
    return json.dumps(PermissionDeniedException().to_json())

# Generic exe handling procedure, on json error
def _handle_exception(ex):
    
    if isinstance(ex, ElementNotFoundException):
        response.status = 404
    elif isinstance(ex, PermissionDeniedException):
        response.status = 403
    else:
        response.status = 400
    
    return ex.to_json()

##############################################################
# # Logic                                                    #
##############################################################
@route("/logics")
def get_logics():
    
    logics = config.read_logics();

    # filter logic by rooms 
    if 'filterByRoom' in request.query:
        logics = [logic for logic in logics if logic.room == request.query.filterByRoom]
        
    return {"logics" : array_to_json(logics) }

# Save the logic based on json and id
def _save_logic(json_logic, id):
      # # get json 
    json_data = json.load(request.body)
    
    if id != None:
        json_data['id'] = id
    
    # check the logic id, if missing generate random
    if 'id' not in json_data:
        json_data['id'] = 'logic' + str(random.randint(1, 10000))
    try:  
        # create the logic object 
        logic = Logic.build_object_from(json_data)
                        
        # validate 
        rooms = config.read_rooms()
        logics = config.read_logics()
        logic.validate_save(rooms, logics)

        config.write_logic(logic)
        
        return logic.to_json()
    except RestException, e:
        return _handle_exception(e)

# Save or create a new logic
@route("/logics", method="POST")
def post_logics():
    return _save_logic(request, None)

# Get detail of a logic
@route("/logics/<id>")
def get_logic(id):
    try:
         # read a single logic 
        return config.read_logic(id).to_json()
    except RestException, e:
        return _handle_exception(e)

# Modify an existing logic
@route("/logics/<id>", method="PUT")
def put_logic(id):
    return _save_logic(request, id)
    
# Delete a logic
@route("/logics/<id>", method="DELETE")
def delete_logic(id):    
    try:
        # # read the room by id
        logic = config.read_logic(id)

        # delete the logic
        config.delete_room(logic)
        
        update_config_logic(config)

        return logic.to_json()
    except RestException, e:
        return _handle_exception(e)

# Enable of disable a logic
def _enable_disable_logic(id, enable):
    try:
         # read a single logic and activate it
        logic = config.read_logic(id)
        logic.enabled = enable
        config.write_logic(logic)
        
        # disable all other logics for room
        disable_logics = [logic_ for logic_ in config.read_logics() if logic_.room == logic.room and logic.id != logic_.id and isinstance(logic, ClimaticLogic)]
        
        for disable_logic in disable_logics:
            disable_logic.enabled = False
            config.write_logic(disable_logic)
        
        update_config_logic(config)
        
        return "ok"
    except RestException, e:
        return _handle_exception(e)

# Activate a logic 
@route("/logics/<id>/commands/enable", method=["POST", "PUT"])
def activate_logics(id):
    return _enable_disable_logic(id, True)

# Disbale a logic
@route("/logics/<id>/commands/disable", method=["POST", "PUT"])
def deactive_logics(id):
    return _enable_disable_logic(id, False)
   
##############################################################
# # maps                                                     #
############################################################## 
@route("/maps")
def get_maps():
    return {"maps" : array_to_json(config.read_rooms()) }      

# Save a room by id
def _save_room(request, id):
    # get the json data 
    json_data = json.load(request.body)

    if id != None:
        json_data['id'] = id
    
    try:
        # create the room object 
        room = Room.build_object_from(json_data)
        
        # validate, the devices 
        devices = config.read_devices()
        room.validate_save(devices)
        
        # save the room 
        config.write_room(room)
        
        update_config_alert(config)

        return room.to_json()
    except RestException, e:
        return _handle_exception(e)

# Create a new room if the room exsist  
@route("/maps", method="POST")
def post_maps():
    return _save_room(request, None)

# get room by id
@route("/maps/<id>")
def get_room(id):
    try:
         # read a single room 
        return config.read_room(id).to_json()
    except RestException, e:
        return _handle_exception(e)
    
# Modify a room by id
@route("/maps/<id>", method="PUT")
def put_room(id):
    return _save_room(request, id)

# Delete a room by id
@route("/maps/<id>", method="DELETE")
def delete_room(id):
    try:
        # read the room by id
        room = config.read_room(id)
        
        # validate delete
        room.validate_delete(config.read_logics())

        # delete the logic
        config.delete_room(room)

        update_config_alert(config)

        return room.to_json()
    except RestException, e:
        return _handle_exception(e)

# Disable logic by id    
def _disable_climat_logic(id):
    disable_logics = [logic for logic in config.read_logics() if logic.room == id and logic.enabled == True and isinstance(logic, ClimaticLogic) ]
    
    for disable_logic in disable_logics:
        disable_logic.enabled = False
        config.write_logic(disable_logic)

    update_config_logic(config)

# Enable the warmup of a room 
@route("/maps/<id>/commands/warmup", method=["POST", "PUT"])
def put_room_command_warp(id):
    try:
        # enable all OnOffDevice
        room = config.read_room(id)

        # disable all other logics for room
        _disable_climat_logic(id)
        
        # select the devices
        devices = [device for device in config.read_devices() if device.type == "OnOff" and device.id in room.devices] 
         
        for device in devices:
            _execute_command(device.id, 'on')
        return "ok"
    except RestException, e:
        return _handle_exception(e)

# Close the warup/
@route("/maps/<id>/commands/off", method=["POST", "PUT"])
def put_room_command_off(id):
    try:
        # enable all OnOffDevice
        room = config.read_room(id)
        
        # disable all other logics for room
        _disable_climat_logic(id)

        # select the devices
        devices = [device for device in config.read_devices() if device.type == "OnOff" and device.id in room.devices] 
         
        for device in devices:
            _execute_command(device.id, 'off')
            
        return "ok"
    except RestException, e:
        return _handle_exception(e)    
       
##############################################################
# # devices                                                     #
############################################################## 
@route("/devices")
def get_devices():
    return {"devices" : array_to_json(config.read_devices()) }    

def _save_device(request, id):
    # get the json data 
    json_data = json.load(request.body)
    
    if id != None:
        json_data['id'] = id

    try:
        # create the device object 
        device = Device.build_object_from(json_data)
        
        # validate, the rooms 
        rooms = config.read_rooms()
        
        # validate the device
        device.validate_save()
        
        # save the drain 
        config.write_device(device)
        
        update_config_modbus(config)
        
        return device.to_json()
    except RestException, e:
        return _handle_exception(e)

@route("/devices", method="POST")
def post_devices():
    return _save_device(request, None)
        
@route("/devices/<id>")
def get_device(id):
    try:
         # read a single device 
        return config.read_device(id).to_json()
    except RestException, e:
        return _handle_exception(e)
    
@route("/devices/<id>", method="PUT")
def put_device(id):   
    return _save_device(request, id)
        
@route("/devices/<id>", method="DELETE")
def delete_device(id):
    try:
        # # read the device by id
        device = config.read_device(id)
       
        # validate delete 
        device.validate_delete(config.read_rooms())
 
         # delete the logic
        config.delete_device(device)

        return device.to_json()
    except RestException, e:
        return _handle_exception(e)
    
    
def _execute_command(id, command):
    try:
         # read a single logic and activate it
        device = config.read_device(id)
        
        daemon_config = config.read_daemon_config()

        if device.type != 'OnOff':
            raise ElementNotFoundException()
        
        if command == "on":
            write_coil(device, daemon_config, True)
        else:
            write_coil(device, daemon_config, False)
        return "ok"
    except RestException, e:
        return _handle_exception(e)
    
@route("/devices/<id>/commands/on", method=["POST", "PUT"])
def on_device(id):
    return _execute_command(id, "on")

@route("/devices/<id>/commands/off", method=["POST", "PUT"])
def off_device(id):
    return _execute_command(id, "off")

##############################################################
# # status                                                      #
############################################################## 
@route("/status")
def get_status():
    devices = config.read_devices()
     
    daemon_config = config.read_daemon_config()
    try: 
        list = get_device_status_list(devices, daemon_config)
        return {"status" : array_to_json(list)   }
    except RestException, e:
        return _handle_exception(e)

@route("/status/<id>")
def get_state(id):
    # get device
    device = config.read_device(id)
    
    daemon_config = config.read_daemon_config()

    # create the device status
    try: 
        status = get_device_status(device, daemon_config)
        return status.to_json()
    except RestException, e:
        return _handle_exception(e)    

##############################################################
# # config                                                     #
############################################################## 
@route("/config")
def get_config():
    config_dev = config.read_config()
    mail_config = config.read_mail_config()
    alert_config = config.read_alert_config()
    daemon_config = config.read_daemon_config()
    logic_config = config.read_logic_config()
    sec_config = config.read_sec_config()
    
    if config_dev == None:
        # create new default configuration 
        config_dev = Config()
        config.write_config(config_dev)
                
    if mail_config == None:
        # create new mail default configuration 
        mail_config = MailConfig()
        config.write_mail_config(mail_config)
        
    if alert_config == None:
        # create new alert default configuration 
        alert_config = AlertConfig()
        config.write_alert_config(alert_config)
        
    if daemon_config == None:
        # create new daemon default configuration 
        daemon_config = DaemonConfig()
        config.write_daemon_config(daemon_config)
        
    if logic_config == None:
        # create new daemon default configuration 
        logic_config = LogicConfig()
        config.write_logic_config(logic_config)
        
    if sec_config == None:
        # create new security default configuration 
        sec_config = SecurityConfig()
        config.write_sec_config(sec_config)
       
    return {"config" : { "plant" :  config_dev.to_json(), "mail" : mail_config.to_json() , "alert" : alert_config .to_json(), "daemon" : daemon_config.to_json(), "logic": logic_config.to_json(), "security" : sec_config.to_json() } }      


@route("/config", method="POST")
def post_config():
    # # get the json data 
    json_data = json.load(request.body)

    try:
        # work on different configuration
        if "plant" in json_data:
            # create the device object 
            config_dev = Config.build_object_from(json_data["plant"])
      
            # save the data 
            config.write_config(config_dev)
            
        if "mail" in json_data:
            # create the device object 
            mail_config_dev = MailConfig.build_object_from(json_data["mail"])
      
            # save the data 
            config.write_mail_config(mail_config_dev)
            
        if "alert" in json_data:
            # create the device object 
            alert_config_dev = AlertConfig.build_object_from(json_data["alert"])
      
            # save the data 
            config.write_alert_config(alert_config_dev)
            
            update_config_alert(config)
            
        if "daemon" in json_data:
            # create the device object 
            daemon_config_dev = DaemonConfig.build_object_from(json_data["daemon"])
      
            # save the data 
            config.write_daemon_config(daemon_config_dev)
            
            update_config_modbus(config)
            
        if "logic" in json_data:
            # create the device object 
            logic_config_dev = LogicConfig.build_object_from(json_data["logic"])
      
            # save the data 
            config.write_logic_config(logic_config_dev)
            
        if "security" in json_data:
            # create the device object 
            security_config_dev = SecurityConfig.build_object_from(json_data["security"])
      
            # save the data 
            config.write_sec_config(security_config_dev)
        
        return get_config()
    except RestException, e:
        return _handle_exception(e)

@route("/config/reload", method="GET")
def relaod_config():
    config.reload()
    update_config_logic(config)
    update_config_modbus(config)
    update_config_alert(config)
    return "ok"

#############################################################
#  services                                                  #
############################################################## 
@route("/services", method="GET")
def list_services():
    return { "services" :array_to_json(read_service_status(config)) }

##############################################################
#  options                                                   #
############################################################## 
def options():
    return "ok"

def options_id(id):
    return "ok"

# Read the configuration
config = MynaConfig() 

def setup_routing(app):
    app.route('/', ['OPTIONS'], options)
    app.route('/logics', ['OPTIONS'], options)
    app.route('/logics/<id>', ['OPTIONS'], options_id)
    app.route('/logics/<id>/commands/activate', ['OPTIONS'], options_id)
    app.route('/logics/<id>/commands/deactivate', ['OPTIONS'], options_id)
    app.route('/maps', ['OPTIONS'], options)
    app.route('/maps/<id>', ['OPTIONS'], options_id)
    app.route('/maps/<id>/commands/warmup', ['OPTIONS'], options_id)
    app.route('/maps/<id>/commands/off', ['OPTIONS'], options_id)
    app.route('/devices', ['OPTIONS'], options)
    app.route('/devices/<id>', ['OPTIONS'], options_id)
    app.route('/devices/<id>', ['OPTIONS'], options_id)
    app.route('/devices/<id>/commands/on', ['OPTIONS'], options_id)
    app.route('/devices/<id>/commands/off', ['OPTIONS'], options_id)

app = default_app()
setup_routing(app)
app = Gzipper(app, content_types=set(['text/plain', 'text/html', 'text/css',
'application/json', 'application/x-javascript', 'text/xml',
'application/xml', 'application/xml+rss', 'text/javascript',
'image/svg', 'image/svg+xml'])) 
