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
import ConfigParser
import logging
import sys
import os, fcntl
import time
from exception import *

logger = logging.getLogger(__name__)

def config_array_to_string(array):
    return ",".join(array)

def config_string_to_array(string):
    return string.split(',')

TIME_FORMAT = "%H:%M"

def config_time_to_string(time_v):
    return time.strftime(TIME_FORMAT, time_v)

def config_string_to_time(string):
    return time.strptime(string, TIME_FORMAT)

def json_time_to_string(time_c):
    return time.strftime(TIME_FORMAT, time_c)

def json_string_to_time(string):
    return time.strptime(string, TIME_FORMAT)

# Myna configuration file 
class MynaConfig():
       
    def __init__(self):
        self.cfgfile = '/home/paolo/regulation/myna.conf'  # Configuration file
        self.logics = None
        self.rooms = None
        self.devices = None
        self.logics = None
        self.config = None
        self.mail_config = None
        self.daemon_config = None
        self.alert_config = None
        self.logic_config = None
        self.sec_config = None
        
    def reload(self):
        self.logics = None
        self.rooms = None
        self.devices = None
        self.logics = None
        self.config = None
        self.mail_config = None
        self.daemon_config = None
        self.alert_config = None
        self.logic_config = None
        self.sec_config = None
        self.read_logics()
        self.read_rooms()
        self.read_devices()
        self.read_logics()
        self.read_config()
        self.read_mail_config()
        self.read_daemon_config()
        self.read_alert_config()
        self.read_logic_config()
        self.read_sec_config()

    
    ##############################################################
    # # logic                                                     #
    ##############################################################
    # Read all logic 
    def read_logics(self):
        if self.logics == None:
            self.logics = self._read_config(Logic)
        return self.logics
    
    # read a logic by id 
    def read_logic(self, id):
        # read all logic 
        logics = self.read_logics()
        
        for logic in logics:
            if logic.id == id:
                return logic
        raise ElementNotFoundException()
    
    def write_logic(self, logic):
        logic = self._write_config(logic)
        self.reload()
        return logic
    
    def delete_logic(self, logic):
        logic = self._delete_config(logic)
        self.reload()
        return logic
    
    ##############################################################
    # # rooms                                                    #
    ##############################################################
    def read_rooms(self):
        if self.rooms == None:
            self.rooms = self._read_config(Room)
        return self.rooms
    
    # read a logic by id 
    def read_room(self, id):
        # read all logic 
        rooms = self.read_rooms()
        
        for room in rooms:
            if room.id == id:
                return room
        raise ElementNotFoundException()
    
    def write_room(self, room):
        room = self._write_config(room)
        self.reload()
        return room
    
    def delete_room(self, room):
        room = self._delete_config(room)
        self.reload()
        return room
    
    ##############################################################
    # # device                                                    #
    ##############################################################
    def read_devices(self):
        if self.devices == None:
            self.devices = self._read_config(Device)
        return self.devices
    
    # read a device by id 
    def read_device(self, id):
        # read all logic 
        devices = self.read_devices()
        
        for device in devices:
            if device.id == id:
                return device
        raise ElementNotFoundException()
    
    def write_device(self, device):
        device = self._write_config(device)
        self.reload()
        return device
    
    def delete_device(self, device):
        device = self._delete_config(device)
        self.reload()
        return device
    
    ##############################################################
    # configuration                                              #
    ##############################################################
    def read_config(self):
        if self.config == None:
            self.config = self._read_config(Config)
        return self.config
       
    def write_config(self, config):
        config = self._write_config(config)
        self.reload()
        return config
    
    def read_mail_config(self):
        if self.mail_config == None:
            self.mail_config = self._read_config(MailConfig)
        return self.mail_config
       
    def write_mail_config(self, mailConfig):
        mailConfig = self._write_config(mailConfig)
        self.reload()
        return mailConfig
    
    def read_alert_config(self):
        if self.alert_config == None:
            self.alert_config = self._read_config(AlertConfig)
        return self.alert_config
       
    def write_alert_config(self, alertConfig):
        alertConfig = self._write_config(alertConfig)
        self.reload()
        return alertConfig
    
    def read_daemon_config(self):
        if self.daemon_config == None:
             self.daemon_config = self._read_config(DaemonConfig)
        return self.daemon_config
       
    def write_daemon_config(self, daemonConfig):
        daemonConfig = self._write_config(daemonConfig)
        self.reload()
        return daemonConfig
    
    def read_logic_config(self):
        if self.logic_config == None:
             self.logic_config = self._read_config(LogicConfig)
        return self.logic_config
       
    def write_logic_config(self, logic_config):
        logic_config = self._write_config(logic_config)
        self.reload()
        return logic_config
    
    def read_sec_config(self):
        if self.sec_config == None:
             self.sec_config = self._read_config(SecurityConfig)
        return self.sec_config
    
    def write_sec_config(self, sec_config):
        sec_config = self._write_config(sec_config)
        self.reload()
        return sec_config
        
    def _read_config(self, type):
        # This function write the logic to the configuration file 
        logger.info("Read configuration for type %s and file %s", type, self.cfgfile)
        
        fd = None
        try:
            # open the configuration file 
            fd = open(self.cfgfile)
            # lock the file 
            fcntl.flock(fd, fcntl.LOCK_SH)
            
            config = ConfigParser.ConfigParser()
            config.readfp(fd)
            
            # check single on multiple section name 
            if issubclass(type, MultipleSectionConfigClass):
                list = []
                # cycle on all section 
                for section in config.sections():
                    if section.startswith(type.section_name):
                        logger.debug('found multi section %s of type %s', section, type)            
                        
                        # # split the id 
                        split = section.split('.')               
                    
                        if (len(split) == 2):
                            # configuration id
                            id = split[1]
                            
                            # call the static version of new instance
                            obj = type._new_instance(section, config)
                            
                            if obj == None:
                                # the instance method return none, create it form type
                                obj = type() 
                                
                            # start parsing
                            obj.parse_config(section, config, "")

                            # append the object 
                            list.append(obj)
                
                return list
            else:
                # cycle on all section 
                for section in config.sections():
                    if type.section_name in section:
                        logger.debug('found simple section %s of type %s', section, type)            
                        
                        # call the static version of new instance
                        obj = type._new_instance(section, config)
                        
                        if obj == None:
                            # the instance method return none, create it form type
                            obj = type() 
                            
                        # start parsing
                        obj.parse_config(section, config, "")
                        return obj
               
        except ConfigParser.ParsingError, e:
            print e
            sys.exit(1)
        finally:
            if fd != None:
                fd.close()             
 
    def _write_config(self, obj):
        # This function write the logic to the configuration file 
        logger.info("Write the obj to configuration %s", obj)
        
        fd = None
        try:
            # open the configuration file 
            fd = open(self.cfgfile, 'r+w')
            # lock the file 
            fcntl.flock(fd, fcntl.LOCK_EX)
            
            config = ConfigParser.ConfigParser()
            config.readfp(fd)
            
            # count the section name 
            section_name = obj.section_name
            
            if isinstance(obj, MultipleSectionConfigClass):
                section_name = obj.section_name + "." + obj.id
                        
            # remove the 
            self._remove_section(section_name, config)
 
            # add the section and write config 
            config.add_section(section_name)
            obj.write_config(section_name, config, "")
             
            # write the config file 
            fd.seek(0)
            fd.truncate()
            config.write(fd)                 
        except ConfigParser.ParsingError, e:
            sys.exit(1)
        finally:
           if fd != None:
               fd.close()  
    
    def _delete_config(self, obj):
        # This function write the room to the configuration file 
        logger.info("remove the object from configuration %s", obj)

        fd = None
        try:
            # open the configuration file 
            fd = open(self.cfgfile, 'r+w')
            # lock the file 
            fcntl.flock(fd, fcntl.LOCK_EX)
            
            config = ConfigParser.ConfigParser()
            config.readfp(fd)
                        
            # count the section name 
            section_name = obj.section_name
            
            if isinstance(obj, MultipleSectionConfigClass):
                section_name = obj.section_name + "." + obj.id
                        
            # remove the 
            self._remove_section(section_name, config)
             
            # write the config file 
            fd.seek(0)
            fd.truncate()
            config.write(fd)           
        except ConfigParser.ParsingError, e:
            sys.exit(1)
        finally:
           if fd != None:
               fd.close()   
            
    def _remove_section(self, id_section, config):
        if config.has_section(id_section):
                logger.debug("Found the section %s section id ... remove it", id_section)
                config.remove_section(id_section)

# Configuration class
class ConfigClass():
    
    types = None
    
    @staticmethod
    def _new_instance(section_name, config):
        return None
    
    def parse_config(self, section, config, parentKey):
        logger.debug("start parsing config for class %s", self)
        
        # cycle on all type 
        for key, tupleType in self.types.items():
            
            # extract tuple
            readKey = key
            if parentKey != "":
                readKey = parentKey + "." + key
            value = None 
            type, isArray, isRequired = tupleType
            
            logger.debug("\t try to parse config tuple name %s definition %s", key, tupleType)

            hasOptions = config.has_option(section, readKey)
           
            if type in ['time', 'string', 'int', 'float', 'boolean']: 
                if type == "string" and not isArray and hasOptions:
                    value = config.get(section, readKey)
                    
                if type == "string" and isArray and hasOptions:
                    value = config_string_to_array(config.get(section, readKey))
                    
                if type == "boolean" and hasOptions:
                    value = config.getboolean(section, readKey)
                    
                if type == "int" and hasOptions:
                    value = config.getint(section, readKey)
                    
                if type == "float" and hasOptions:
                    value = config.getfloat(section, readKey)
                    
                if type == "time" and hasOptions:
                    value = config_string_to_time(config.get(section, readKey))

                if value != None:
                    logger.debug("\t found value %s for key %s", value, key)
                    
                    # assign the value to the variable 
                    setattr(self, key, value)
            else:
                if isArray:
                    items = config.options(section)
                    list = []
                    for i in range(0, 100):
                        elKey = readKey + '[' + str(i) + ']'        
                                   
                        if any(elKey in s for s in items):
                            # found the value 
                            newObj = eval(type)()
                            newObj.parse_config(section, config, elKey)
                            list.append(newObj)
                        else:
                            break
                    setattr(self, key, list)
                else:
                    newObj = eval(type)()
                    newObj.parse_config(section, config, readKey)
                    setattr(self, key, newObj)

    def write_config(self, section, config, parentKey):
        # cycle on all type 
        for key, tupleType in self.types.items():
            
            # extract tuple
            type, isArray, isRequired = tupleType
            
            logger.debug("\t try to write config tuple name %s definition %s parent key %s", key, tupleType, parentKey)
            
            value = getattr(self, key)
           
            if parentKey != "":
                key = parentKey + "." + key
                               
            if type in ['time', 'string', 'int', 'float', 'boolean']:
              
                if type == "string" and not isArray:
                    if value != None:
                        config.set(section, key, value)
      
                if type == "string" and isArray:
                    if len(value) > 0:
                        config.set(section, key, config_array_to_string(value))
                    
                if type == "boolean"  and value != None:
                    config.set(section, key, value)
                                
                if type == "int"  and value != None:
                    config.set(section, key, value)
                        
                if type == "float" and value != None:
                    config.set(section, key, value)
                                   
                if type == "time" and value != None:
                    config.set(section, key, config_time_to_string(value))
            else:
                if not isArray:
                    # call sub writer config                   
                    value.write_config(section, config, key)
                else:
                    # call sub writer config
                    for element in value:
                        index = value.index(element) 
                        elKey = key + '[' + str(index) + ']'
                        if parentKey != "":
                            elKey = parentKey + "." + key                          
                        element.write_config(section, config, elKey)
                
    def to_json(self):
        dict = {}
         # cycle on all type 
        for key, tupleType in self.types.items():
            
            # extract tuple
            type, isArray, isRequired = tupleType
            
            value = getattr(self, key)
            
            if isArray:
                array = [self._convert_json(type, el) for el in value ]
                value = array
            else:
                value = self._convert_json(type, value)     
                    
            if value != None:
                dict[key] = value
                            
        return dict
    
    def _convert_json(self, type, value):
        if type in ['time', 'string', 'int', 'float', 'boolean']:   
            if type == 'time' and value != None:
                value = json_time_to_string(value)
            return value
        else:
            return value.to_json()
   
    def from_json(self, json):
          for key, tupleType in self.types.items():
            
            # extract tuple
            type, isArray, isRequired = tupleType
                  
            # first check required flag 
            if isRequired:
                if key not in json:
                    raise MissingParamException(key)
                
                # add empty check 
                if (not json[key] and not isinstance(json[key], int)):
                   raise MissingParamException(key)
           
            value = None
            if key in json:
                value = json[key]

            # check data array
            if isArray:
                if not isinstance(value, list):
                    raise InvalidParamException(key)
                
            # check if is simple type 
            if not isArray:
                value = self._convert_from_json(type, value)
                    
                # assign the value
                if value != None:
                    setattr(self, key, value)
            else:
                array = [self._convert_from_json(type, el) for el in value ]
                value = array
                setattr(self, key, value)
    
    def _convert_from_json(self, type, value): 
        if type in ['time', 'string', 'int', 'float', 'boolean']:

                if type == "time" and value != None:
                    value = json_string_to_time(value)
                    
                if type == "int" and value != None:
                    # check type 
                    if not isinstance(value, int):
                        raise InvalidParamException(key)
                    
                if type == "float" and value != None:
                    # check type 
                    if not (isinstance(value, float) or isinstance(value, int)):
                        raise InvalidParamException(key)
                
                if type == "string" and value == '':
                    value = None

                return value
        else:
            newObj = eval(type)()
            newObj.from_json(value)
            return newObj
  
class MultipleSectionConfigClass(ConfigClass):
    pass

class Room(MultipleSectionConfigClass):
    
    section_name = "room"
    
    types = {
             # "name" : (the data type, is array, is required)
             "id" : ("string", False, True),
             "name" : ("string", False, False),
             "devices" : ("string", True, True),
             "external" : ("boolean", False, False),
             "climatic" : ("ClimaticRoomConfig", False, False),
             "alert" : ("AlertRoomConfig", False, False)
            }
    
    def __init__(self):
        self.id = None
        self.name = None
        self.devices = []
        self.external = False 
        self.alert = AlertRoomConfig()
        self.climatic = ClimaticRoomConfig()
        
    @staticmethod
    def build_object_from(json):
        # # create the new object 
        obj = Room()
        obj.from_json(json)
        return obj
    
    def validate_save(self, devices):
        if len(self.devices) == 0:
            raise MissingParamException('devices')
       
        # check the devices are valid
        list_id = [device.id for device in devices] 
        
        matching = [s for s in self.devices if s in list_id]
        
        if len(matching) != len(self.devices):
            raise InvalidParamException('devices')
        
        # checking for external devices
        matching = [device.id for device in devices if device.id in self.devices and ((hasattr(device, 'external') and self.external == device.external) or not hasattr(device, 'external'))]
      
        if len(matching) != len(self.devices):
            raise InvalidExternalDeviceException()
        
    def validate_delete(self, logics):
        # validate delete can be done only if no logic use the room 
        list_id = [logic.room for logic in logics]        
                   
        if self.id in list_id:
            raise ElementUsedException('logic') 
        
class AlertRoomConfig(ConfigClass): 
    def __init__(self):
        self.tupper = None
        self.tlower = None
    
    types = {
             # "name" : (the data type, is array, is required)
             "tupper" : ("int", False, False),
             "tlower" : ("int", False, False)
            }    
    
    
class ClimaticRoomConfig(ConfigClass): 
    def __init__(self):
        self.x = 4.0
        self.y = 12.0
        self.k = 0.01
    
    types = {
             # "name" : (the data type, is array, is required)
             "x" : ("float", False, False),
             "y" : ("float", False, False),
             "k" : ("float", False, False)
            }  
    
class Logic(MultipleSectionConfigClass):
    
    section_name = "logic"
    
    types = {
             # "name" : (the data type, is array, is required)
             "id" : ("string", False, True),
             "room" : ("string", False, True),
             "type" : ("string", False, True),
             "enabled" : ("boolean", False, False) 
            }

    def __init__(self):
        self.id = None
        self.enabled = False
        self.room = None
        
    @staticmethod
    def _new_instance(section_name, config):
        type = config.get(section_name, "type")                     
                          
        if type == 'ThresholdTemperature':
            return ThresholdTemperatureClimaticLogic()   
                               
        if type == 'TimeProgramming':
            return TimeProgrammingLogic()
        return None
    
    
    @staticmethod
    def build_object_from(json):
        # first step, try to load the type
        if 'type' in json:
            # # get the type
            type = json['type']
            obj = None
            
            if type == 'ThresholdTemperature':
                obj = ThresholdTemperatureClimaticLogic()   
                               
            if type == 'TimeProgramming':
                obj = TimeProgrammingLogic()  
                
            if obj == None:
                raise InvalidParamException('type') 
        else:
            raise MissingParamException('type')
        
        obj.from_json(json)
        return obj
    
    def validate_save(self, rooms, logics):       
        # check the rooms are defines
        list_id = [room.id for room in rooms]       
        if self.room not in list_id:
            raise InvalidParamException('room')   
        
        # save the enabled 
        self.enabled = False
        for logic in logics :
            if logic.id == self.id:
                self.enabled = logic.enabled
                
class ClimaticLogic(Logic):

    def validate_save(self, rooms, logics):
        Logic.validate_save(self, rooms, logics)
        # # check the logic type  type logic 
        already_present = [logic for logic in logics if self.type == logic.type and self.id != logic.id and logic.room == self.room]
        
        if len(already_present) > 0:
            raise LogicTypeAlreadyPresentException(self.type)
             
class ThresholdTemperatureClimaticLogic(ClimaticLogic):

    type = 'ThresholdTemperature'
    
    types = {
             # "name" : (the data type, is array, is required)
             "temp" : ("MeasureConfig", False, True),
             }
    
    def __init__(self):
        ClimaticLogic.__init__(self)
        self.temp = MeasureConfig(0)
        self.types.update(Logic.types)

class TimeProgrammingLogic(ClimaticLogic):

    type = 'TimeProgramming'
    
    types = {
             # "name" : (the data type, is array, is required)
             "time" : ("TimeProgram", True, True),
             }
        
    def __init__(self):
        ClimaticLogic.__init__(self)
        self.time = [TimeProgram()]
        self.types.update(Logic.types)        
        
    def validate_save(self, rooms, logics):
        ClimaticLogic.validate_save(self, rooms, logics)
        
        valid_time = {}
        
        # time validation for day 
        for time_program in self.time:
            # first validate the time start and stop 
            if time_program.start >= time_program.stop:
                raise InvalidParamException('time')   
            
            # check the day of week
            for day in time_program.days: 
                if day not in time_program.DAYS:
                    raise InvalidParamException('time.days')   
                       
            # cycle on all logics 
            for other_time in self.time:
                if other_time != time_program:
                    # check for each day 
                    for day in other_time.days:
                        # check the day 
                        if day in time_program.days:
                            # now test time range start and end 
                            if time_program.start >= other_time.start and time_program.start <= other_time.stop:
                                raise TimeProgrammingOverlapException()   
                            if time_program.stop >= other_time.start and time_program.stop <= other_time.stop:
                                raise TimeProgrammingOverlapException()  
# ##
# # Simple measure box container 
# ##
class MeasureConfig(ConfigClass):
    
    def __init__(self, value=0):
        self.unit = 'C'
        self.value = value
    
    types = {
             # "name" : (the data type, is array, is required)
             "value" : ("int", False, True),
             "unit" : ("string", False, False)
            }
    
    
class TimeProgram(ConfigClass):
    
     types = {
                "days" : ("string", True, True),
                "start" : ("time", False, True),
                "stop" : ("time", False, True),
                "temp" : ("MeasureConfig", False, True)

             }
        
     DAYS = [ "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    
     def __init__(self):
         self.start = None
         self.stop = None
         self.days = []
         self.temp = MeasureConfig(0)

  
class Device(MultipleSectionConfigClass):
    
    section_name = "device"
       
    types = {
             # "name" : (the data type, is array, is required)
             "id" : ("string", False, True),
             "type" : ("string", False, True),
             "name" : ("string", False, False),
             "bus" : ("string", False, True),
            }

    def __init__(self):
        self.id = None
        self.type = None
        self.name = None  
        self.bus = None
        
        
    @staticmethod
    def _new_instance(section_name, config):
        type = config.get(section_name, "type")    
        bus = config.get(section_name, "bus")                             
        
        # create instance based on device/type and bus
        if type == 'Temperature' :
            if bus == "onewire":
                return OneWireTemperatureDevice()
            if bus == "enocean":
                return EnoceanTemperatureDevice()
                
            return TemperatureDevice()   
        
        if type == 'OnOff':
            return PiFaceOnOffDevice()   
                               
        return None     
        
    @staticmethod
    def build_object_from(json):
         # first step, try to load the type
        if 'type' in json:
            # # get the type
            type = json['type']
            bus = json['bus']
            obj = None
            
            if type == 'Temperature':
                if bus == "onewire":
                    obj = OneWireTemperatureDevice()
                elif bus == "enocean":
                    obj = EnoceanTemperatureDevice()
                else:
                    obj = TemperatureDevice()   
                
            if type == 'OnOff':
                obj = PiFaceOnOffDevice()   
                
            if obj == None:
                raise InvalidParamException('type') 
        else:
            raise MissingParamException('type')
        
        obj.from_json(json)
        return obj
    
    def validate_save(self):
        pass
    
    def validate_delete(self, rooms):
        # # validate delete can be done only if no room use the device 
        list_id = [name for room in rooms for name in room.devices]        
                   
        if self.id in list_id:
            raise ElementUsedException('room')     
        
class TemperatureDevice(Device):
    types = { "register" : ("int", False, True), "external" : ("boolean", False, False)}
    
    def __init__(self):
        Device.__init__(self)
        self.register = None
        self.external = False
        self.types.update(Device.types)
        
class OneWireTemperatureDevice(TemperatureDevice):
    types = { "address" : ("string", False, True) }
    
    def __init__(self):
        TemperatureDevice.__init__(self)
        self.bus = "onewire"
        self.address = None
        self.types.update(TemperatureDevice.types)
        
class EnoceanTemperatureDevice(TemperatureDevice):
    types = { "eep" : ("string", False, True), "address" : ("string", False, True) }
    
    def __init__(self):
        TemperatureDevice.__init__(self)
        self.bus = "enocean"
        self.eep = None
        self.address = None
        self.types.update(TemperatureDevice.types)
        
class OnOffDevice(Device):
    types = { "coil" : ("int", False, True)}
    
    def __init__(self):
        Device.__init__(self)
        self.coil = None
        self.types.update(Device.types)        
        
class PiFaceOnOffDevice(OnOffDevice):
    
    def __init__(self):
        OnOffDevice.__init__(self)
        self.bus = "piface"
        
class Config(ConfigClass):
    
    section_name = "plant"
        
    types = {
             # "name" : (the data type, is array, is required)
             "plantid" : ("string", False, True),
             }

    @staticmethod
    def build_object_from(json):
        # # create the new object 
        obj = Config()
        obj.from_json(json)
        return obj
    
    def __init__(self):
        self.plantid = "0123456789"
        
class BaseDaemonClass(ConfigClass):
    
    types = {
         # "name" : (the data type, is array, is required)
         "pidfile" : ("string", False, False)
         }
        
    def __init__(self):
        self.pidfile = None

class MailConfig(ConfigClass):
    
    section_name = "mail"
        
    types = {
             # "name" : (the data type, is array, is required)
             "smtp" : ("string", False, True),
             "from_address" : ("string", False, False)
             }

    @staticmethod
    def build_object_from(json):
        # # create the new object 
        obj = MailConfig()
        obj.from_json(json)
        return obj
    
    def __init__(self):
        self.smtp = 'localhost'
        self.from_address = ""
        
class LogicConfig(BaseDaemonClass):
    
    section_name = "daemon.Logic"
    
    @staticmethod
    def build_object_from(json):
        # # create the new object 
        obj = LogicConfig()
        obj.from_json(json)
        return obj
   
    def __init__(self):
        BaseDaemonClass.__init__(self)
        self.types.update(BaseDaemonClass.types)
        self.pidfile = "/var/run/myna/logic.pid"
        
class AlertConfig(BaseDaemonClass):
    
    section_name = "alert"
        
    types = {
             # "name" : (the data type, is array, is required)
             "temperature_tupper" : ("int", False, True),
             "temperature_tlower" : ("int", False, True),
             "temperature_mail_to" : ("string", False, False),  # comma separated list
             "unable_mail_to" : ("string", False, False),  # comma separated list
             "temperature_enable" : ("boolean", False, True),
             "unable_enable" : ("boolean", False, True)
             }

    @staticmethod
    def build_object_from(json):
        # # create the new object 
        obj = AlertConfig()
        obj.from_json(json)
        return obj
    
    def __init__(self):
        BaseDaemonClass.__init__(self)
        self.types.update(BaseDaemonClass.types)
        self.pidfile = "/var/run/myna/alert.pid"
        self.temperature_tupper = 100
        self.temperature_tlower = -100
        self.temperature_mail_to = ""
        self.unable_mail_to = ""
        self.temperature_enable = True
        self.unable_enable = True
                
class DaemonConfig(ConfigClass):
    
    section_name = "daemon.Daemon"
        
    types = {
             # "name" : (the data type, is array, is required)
             "ListenAddress" : ("string", False, False),
             "ListenPort" : ("int", False, False),
             "uid" : ("int", False, False),
             "gid" : ("int", False, False),
             "supplementarygroups" : ("boolean", False, False),
             "pidfile" : ("string", False, False)
             }

    @staticmethod
    def build_object_from(json):
        # # create the new object 
        obj = DaemonConfig()
        obj.from_json(json)
        return obj
    
    def __init__(self):
        self.ListenAddress = '0.0.0.0'
        self.ListenPort = 502
        self.uid = 502
        self.gid = 502
        self.supplementarygroups = True
        self.pidfile = '/run/modbus/modbus.pid'
        
    def getGwAddress(self):
        if self.ListenAddress == '0.0.0.0':
            return "localhost"
        return self.ListenAddress


class SecurityConfig(ConfigClass):
    
    section_name = "security"
        
    types = {
             # "name" : (the data type, is array, is required)
             "allow" : ("string", False, False),
             "deny" : ("string", False, False),
             }

    @staticmethod
    def build_object_from(json):
        # # create the new object 
        obj = SecurityConfig()
        obj.from_json(json)
        return obj
    
    def __init__(self):
        self.allow = ""
        self.deny = ""
