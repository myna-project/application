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
import logging 
from config import MynaConfig
from status import get_device_status_list, DeviceStatus

import smtplib
from email.mime.text import MIMEText
from mail import send_mail

# load the configuration file 
config = MynaConfig()

logger = logging.getLogger('alarm')

# notification type list 
UNABLE_TO_READ_VALUE = 9999

# generic notification 
class Notification():
    def __init__(self, device=None, state=None, room=None):
        self.device = device
        self.state = state
        self.room = room
  
    def getSubject(self):
        return "None"
    def getMsg(self):
        return "None"
    
    def getDeviceName(self):
        if self.device.name != None and self.device.name != '':
            return self.device.name
        return self.device.id    
        
    def getRoomName(self):
        if self.room == None:
            return None
        if self.room == None:
            return ""
        if self.room.name != None and self.room.name != '':
            return self.room.name
        return self.room.id
    
    def getKey(self):
        key = self.type
        
        if self.state != None:
            key += self.state.id
            
        if self.room != None:
            key += self.room.id
        
        return key

# generic alarm notification 
class AlarmNotification(Notification):
    def getSubject(self):
        return "Errore"
class DeAlarmNotification(Notification):        
    def getSubject(self):
        return "ALL WELL"

# notification for unable to read         
class UnableToReadAlarmNotification(AlarmNotification):
    type = "UnableTo"   
    def getSubject(self):
        return "[ALERT] - Impossibile leggere i sensori"
    def getMsg(self):
        msg = "Risulta impossibile leggere il sensore '" + self.getDeviceName()
        roomName = self.getRoomName()
        
        if roomName != None:
            msg += "' nella stanza " + self.getRoomName()
        return msg
              
class UnableToReadDeAlarmNotification(DeAlarmNotification):
    type = "UnableTo"
    def getSubject(self):
        return "Ripristino della lettura dei sensori"
    def getMsg(self):
        return "E stata ripristinata la lettura del sensore '" + self.getDeviceName() + "'"
    
class TemperatureTooHighAlarmNotification(AlarmNotification):
    type = "Temperature"
    def getSubject(self):
        return "[ALERT] - Temperatura troppo alta "
    def getMsg(self):
        return "La temperatura nella stanza '" + self.getRoomName() + "' risulta essere troppo alta " + str(self.state.value) + " " + self.state.unit
    
class TemperatureTooLowAlarmNotification(AlarmNotification):
    type = "Temperature"
    def getSubject(self):
        return "[ALERT] - Temperature troppo bassa "
    def getMsg(self):
        return "La temperatura nella stanza '" + self.getRoomName() + "' risulta essere troppo bassa " + str(self.state.value) + " " + self.state.unit
    
class TemperatureDeAlarmNotification(DeAlarmNotification):
    type = "Temperature"
    def getSubject(self):
        return "Ripristino della soglia di temperature"
    def getMsg(self):
        return "La temperatura nella stanza '" + self.getRoomName() + "' risulta essere nel range di validita'"  
    
notification_map = {}

## this function perform alert system checking 
def perform_check():
    logger.info("Alert checking.... ")
    
    # read the configuration 
    try:
        config.reload()
        mail_config = config.read_mail_config()
        alert_config = config.read_alert_config()
        general_config = config.read_config()
        daemon_config = config.read_daemon_config()
        
        # read the devices, and rooms and status 
        devices = config.read_devices()
        rooms = config.read_rooms()

        status = get_device_status_list(devices, daemon_config)
    except:
        return
        
    # create convenient maps 
    devices_map = { device.id : device for device in devices }
    
    # First work on devices checking 
    list = _check_devices(status, devices, rooms)
    
    # check temperature for room 
    list.extend(_check_temperature(status, devices, rooms, alert_config))
         
    # filter the notification (to send only the first non all every polling cycle)  
    real_list = []
    for notification in list:
        # build notification key 
        notification_key = notification.getKey()
        logger.debug("Current notification selected " + str(notification) + "-" + str(notification.state.id) + "-" + notification_key)
                
        # append the alarm notification, if never send 
        if isinstance(notification, AlarmNotification):
            if notification_key not in notification_map:
                # must send alarm
                real_list.append(notification)
                notification_map.update({ notification_key : 1 })
                
        # append the alarm de notification, if never send 
        if isinstance(notification, DeAlarmNotification):
            
            if notification_key in notification_map:
                # must send alarm
                real_list.append(notification)
                notification_map.pop(notification_key, None)       
          
    # send notification to the user, based on priority 
    notification_device_send = []
    for real_notification in real_list:
        logger.debug("Real notification " + str(real_notification))
        _send_alert(real_notification, mail_config, general_config, alert_config)      
        
## check status of devices based on measure 9999
def _check_devices(status, devices, rooms):
    list = []
    
    ## create room -> device maps 
    room_map = { dev_name : room  for room in rooms for dev_name in room.devices }
    devices_map = { device.id : device for device in devices }

    for state in status:
        # get device type 
        device = devices_map[state.id]
        room = None 
        
        if state.id in room_map:
            room = room_map[state.id]

        if device.type == "Temperature":
            # check unable to read
            if state.value == UNABLE_TO_READ_VALUE:
                logging.error("Unable to read temperate of device %s", state.id)
                list.append(UnableToReadAlarmNotification(device=device, room=room, state=state))
                # continue the cycle
                continue
            else:
                logging.info("All ok for temperate of device %s", state.id)
                list.append(UnableToReadDeAlarmNotification(device=device, room=room, state=state))
    return list
                
def _check_temperature(status, devices, rooms, alert_config):
    list = []
    
    devices_map = { device.id : device for device in devices }
    status_map = { state.id : state for state in status }
    
    # cycle on all rooms 
    for room in rooms:
        if not room.external:
            # select the upper and lower limit 
            tupper = alert_config.temperature_tupper
            if room.alert.tupper:
                tupper = room.alert.tupper
                
            tlower = alert_config.temperature_tlower
            if room.alert.tlower:
                tlower = room.alert.tlower
            
            logger.info("check temperature limit for room %s tuppuer %d tlower %d", room.id, tupper, tlower)
            
            # cycle on all device
            for device_id in room.devices:
                device = devices_map[device_id]
                state = status_map[device_id]
                
                if device.type == "Temperature" and state.value != UNABLE_TO_READ_VALUE:
                    if state.value > tupper:
                        list.append(TemperatureTooHighAlarmNotification(room=room, state=state))
                    elif state.value < tlower:
                        list.append(TemperatureTooLowAlarmNotification(room=room, state=state))
                    else:
                        list.append(TemperatureDeAlarmNotification(room=room, state=state))
    
    return list

def _send_alert(notification, mail_config, general_config, alert_config):    
    # work on subject
    subject = notification.getSubject() + " - Impianto " + general_config.plantid         
       
    # work on message  
    message = notification.getMsg()
    
    # work on destination mail address
    to = None 
    if (isinstance(notification, UnableToReadAlarmNotification) or isinstance(notification, UnableToReadDeAlarmNotification)) and alert_config.unable_enable:
        to = alert_config.unable_mail_to
        
    if (isinstance(notification, TemperatureTooHighAlarmNotification) or isinstance(notification, TemperatureTooLowAlarmNotification) or isinstance(notification, TemperatureDeAlarmNotification)) and alert_config.temperature_enable:
        to = alert_config.temperature_mail_to
                
    if to:
        send_mail(subject, message, to, mail_config, general_config) 
