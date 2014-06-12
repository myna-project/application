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
import datetime
import logging
import time

from config import MynaConfig
from status import get_device_status_list, write_coil

# load the configuration file 
config = MynaConfig()

logger = logging.getLogger('logic')

days = {   0 : 'Monday',
           1 : 'Tuesday',
           2 : 'Wednesday',
           3 : 'Thursday',
           4 : 'Friday',
           5 : 'Saturday',
           6 : 'Sunday'
}

# use this dictionary to save the logic must be executed for the room
actual_logic = {}

# use this dictionary to save last value read from sensors
last_status = {}

# use this dictionary to save temporarily the last value read from sensors
# before to put it in the last_status dictionary
temp_status = {}

# value set when it is unable to read temperature value 
UNABLE_TO_READ_VALUE = 9999

def _get_average_external_temp(devices, status_map, daemon_config):
    
    # sum and number of temperature to do an average value
    sum_external_temperature = 0
    count_external_temperature = 0
    
    # set to 1 if error in read external temperature from register
    read_error = 0
    
    for device in devices:
        if device.type == 'Temperature':
            if device.external == True:
                # get status of the device
                status = status_map[device.id];
                
                # sum and count number of Temperature devices
                if status.value != UNABLE_TO_READ_VALUE:
                    sum_external_temperature += status.value
                    count_external_temperature += 1
                
                else:
                    read_error = 1
    
    # check if there is a correct external temperature
    if count_external_temperature != 0:
        logger.info('Average external temperature is ' + str(sum_external_temperature/count_external_temperature))
        return sum_external_temperature/count_external_temperature
    
    # else check if there is been an error on reading external temperature
    elif read_error == 1:
        logger.info('Unable to read value for external temperature')
        return None
    
    # else there isn't a sensor temperature for the external
    else:
        logger.info('There is no sensor for external temperature')
        return None
    
def _get_average_temperature(room, status_map, daemon_config):
    
    # sum and number of temperature to do an average value
    sum_temperature = 0
    count_temperature = 0
    
    # set to 1 if error in read temperature from register
    read_error = 0
    
    # get every devices in the room
    for device_id in room.devices:
        # get the device status from id
        status = status_map[device_id]
            
        if status.type == 'Temperature':
            # sum and count number of Temperature devices
            if status.value != UNABLE_TO_READ_VALUE:
                sum_temperature += status.value
                count_temperature += 1
                
            else:
                read_error = 1
                
    # check if there is a correct temperature
    if count_temperature != 0:
        # save average temperature in temporary list
        temp_status.update({ room.id : sum_temperature/count_temperature })
    
    # else check if there is been an error on reading temperature
    elif read_error == 1:
        temp_status.update({ room.id : UNABLE_TO_READ_VALUE })
        
    logger.info('Temperature in room ' + str(room.name) + ' is ' + str(temp_status.get(room.id)))
    

def _get_onoffdevices_status(room, status_map, daemon_config):
    
    # list OnOff devices
    list_onOffDevices = {}
    
    # get every devices in the room
    for device_id in room.devices:
        # get the device status from id
        status = status_map[device_id]
        
        if status.type == 'OnOff':
            list_onOffDevices.update({ status.id : status.value })
    
    return list_onOffDevices


def _switch_on_devices(devices_map, list_OnOffDevices, daemon_config):
    
    logger.info('Check off devices and switch them on')
    
    for device_id in list_OnOffDevices.keys():
        if list_OnOffDevices.get(device_id) == False:
            device = devices_map[device_id]
            
            logger.info('Switch ON device: ' + str(device.id))
            
            write_coil(device, daemon_config, True)
        else:
            logger.info('Device ' + str(device_id) + ' is already ON')
            
def _switch_off_devices(devices_map, list_OnOffDevices, daemon_config):
    
    logger.info('Check on devices and switch them off')
    
    for device_id in list_OnOffDevices.keys():
        if list_OnOffDevices.get(device_id) == True:
            device = devices_map[device_id]
            
            logger.info('Switch OFF device: ' + str(device.id))
            
            write_coil(device, daemon_config, False)
        else:
            logger.info('Device ' + str(device_id) + ' is already OFF')
            
def _check_variation_temperature(averageTemp, room, devices_map, list_OnOffDevices, daemon_config):
    
    # check if temperature in the room is going down or going up too quickly
    logger.info('Check variation temperature')
    
    if (last_status.has_key(room.id)):
        logger.info('Last average temperature in room ' + room.id + ' is ' + str(last_status.get(room.id)))
        
        if ( (averageTemp-last_status.get(room.id)) / 60 > room.climatic.k ):
            logger.info('Room is heating up too quickly')
            
            _switch_off_devices(devices_map, list_OnOffDevices, daemon_config)
        
        elif ( (averageTemp-last_status.get(room.id)) / 60 < -room.climatic.k ):
            logger.info('Room is cooling down too quickly')
            
            _switch_on_devices(devices_map, list_OnOffDevices, daemon_config)
        
        else:
            logger.info('Temperature is good! Devices are maintained at the previous status')
    
    else:
        logger.info('There is not a temperature for the room yet!')
            
def _check_average_temp_and_threshold(threshold, room, devices_map, averageTemp, list_OnOffDevices, daemon_config):

    # check if average temperature is less than threshold
    # if yes: check devices off and turn them on       
    if ( averageTemp <= threshold ):
        logger.info('Average temperature: ' + str(averageTemp) + ' is less than threshold: ' + str(threshold))
        _switch_on_devices(devices_map, list_OnOffDevices, daemon_config)
    
    # else check if average temperature is more than threshold + 1 
    # if yes: check devices on and turn them off
    elif ( averageTemp > threshold + 1 ):
        logger.info('Average temperature: ' + str(averageTemp) + ' is more than: ' + str(threshold + 1))
        _switch_off_devices(devices_map, list_OnOffDevices, daemon_config)
    
    else:
        logger.info('Average temperature: ' + str(averageTemp) + ' is slightly more than threshold: ' + str(threshold))
        _check_variation_temperature(averageTemp, room, devices_map, list_OnOffDevices, daemon_config)


def _check_time_to_warm_up(today, logic_time):
    
    # minutes left to the start of the window time
    return ( datetime.datetime.strptime(time.strftime("%H:%M", logic_time.start), '%H:%M') - datetime.datetime.strptime(str(today.hour) + ':' + str(today.minute), '%H:%M') ).seconds / 60
    

def _check_time_to_warm_up_day_before(today, logic_time):
    
    # minutes left to the end of the day before 
    beforeDatetimeLeft = ( datetime.datetime.strptime('23:59', '%H:%M') - datetime.datetime.strptime(str(today.hour) + ':' + str(today.minute), '%H:%M') ).seconds / 60
    
    logger.info("Minutes left before end of the day before the day which is in the logic is " + str(beforeDatetimeLeft))
    
    # minutes of the day left to the start of the window time
    DatetimeLeft = ( datetime.datetime.strptime(time.strftime("%H:%M", logic_time.start), '%H:%M') - datetime.datetime.strptime('00:00', '%H:%M') ).seconds / 60

    logger.info("Minutes of the day left before the start of the window time is " + str(DatetimeLeft))
     
    # number of minutes before the start of the window time
    return DatetimeLeft + beforeDatetimeLeft

def _regulate_devices_before_window_time(logic_time, room, devices_map, averageTemp, averageExternalTemp, timeLeft, list_OnOffDevices, daemon_config):
    
    # check if it is necessary to switch on the devices in the time left before the start of the window time
    if averageTemp < logic_time.temp.value:
        if averageExternalTemp:
            logger.info("Differences of temperature from inside outside and threshold correct with coefficient is " + str(((logic_time.temp.value-averageTemp)/room.climatic.x + (logic_time.temp.value-averageExternalTemp)/room.climatic.y) * 60))
      
            if ( timeLeft <= 30 and timeLeft < ( (logic_time.temp.value-averageTemp)/room.climatic.x + (logic_time.temp.value-averageExternalTemp)/room.climatic.y ) * 60 ):
                _switch_on_devices(devices_map, list_OnOffDevices, daemon_config)
        
            else:
                _switch_off_devices(devices_map, list_OnOffDevices, daemon_config)
    
        else:
            logger.info("Differences of temperature from threshold correct with coefficient is " + str(((logic_time.temp.value-averageTemp)/room.climatic.x) * 60 ))

            if ( timeLeft <= 30 and timeLeft < ((logic_time.temp.value-averageTemp)/room.climatic.x) * 60 ):
                _switch_on_devices(devices_map, list_OnOffDevices, daemon_config)
        
            else:
                _switch_off_devices(devices_map, list_OnOffDevices, daemon_config)
    else:
        logger.info('Temperature is already more than threshold')
        _switch_off_devices(devices_map, list_OnOffDevices, daemon_config)

        
def _time_programming_regulation(logic_time, room, devices_map, today, averageTemp, averageExternalTemp, list_OnOffDevices, daemon_config):
    logger.info("timeProgrammingRegulation for room: " + str(room.id) + ' where temperature threshold is ' + str(logic_time.temp.value))
    
    # set next day of week
    if today.weekday() == 6:
        next_day = 0
    else:
        next_day = today.weekday() + 1
        
    # check if today day of week is in the days of logic
    if days[today.weekday()] in logic_time.days:
        # get the start of the window for the day
        window_start = datetime.datetime.strptime(str(today.year)+'-'+str(today.month)+'-'+str(today.day)+' '+time.strftime("%H:%M", logic_time.start), '%Y-%m-%d %H:%M')
        logger.info('Start time ' + str(window_start))
    
        # get the stop of the window for the day
        window_stop = datetime.datetime.strptime(str(today.year)+'-'+str(today.month)+'-'+str(today.day)+' '+time.strftime("%H:%M", logic_time.stop), '%Y-%m-%d %H:%M')
        logger.info('Stop time ' + str(window_stop))
        
        # check if we are in the time window of the logic
        if today >= window_start and today <= window_stop:
            # check temperature respect to the threshold and command devices appropriately         
            logger.info('We are in the time window of the logic')
            
            _check_average_temp_and_threshold(logic_time.temp.value, room, devices_map, averageTemp, list_OnOffDevices, daemon_config)
        
        # else check if we are before the start window of the logic
        elif today < window_start:
            # check if it is necessary to switch on devices to warm up room before the start of window time
            timeLeft = _check_time_to_warm_up(today, logic_time)
            
            logger.info("Total minutes left before start of the time window in the day is " + str(timeLeft))
            
            _regulate_devices_before_window_time(logic_time, room, devices_map, averageTemp, averageExternalTemp, timeLeft, list_OnOffDevices, daemon_config)
        
        # else we are after the time window of the logic
        else:
            logger.info("We are after the time window of the logic")
        
            # check if next day of the week is in the days of logic   
            if days[next_day] in logic_time.days:
                # check if it is necessary to switch on devices to warm up room before the start of the next day's window time
                logger.info("Next day is in the days of logic")
                
                timeLeft = _check_time_to_warm_up_day_before(today, logic_time)
            
                logger.info("Total minutes left before start of the time window in the next day is " + str(timeLeft))
                
                _regulate_devices_before_window_time(logic_time, room, devices_map, averageTemp, averageExternalTemp, timeLeft, list_OnOffDevices, daemon_config)
                
            else:
                logger.info("Next day isn't in the days of logic")
                _switch_off_devices(devices_map, list_OnOffDevices, daemon_config) 
    
    # else check if next day of week is in the days of logic
    elif days[next_day] in logic_time.days:
        # check if it is necessary to switch on devices to warm up room before the start of the next day's time window
        timeLeft = _check_time_to_warm_up_day_before(today, logic_time)

        logger.info("Total minutes left before start of the next day's time window is " + str(timeLeft))
        
        _regulate_devices_before_window_time(logic_time, room, devices_map, averageTemp, averageExternalTemp, timeLeft, list_OnOffDevices, daemon_config)
    
    # else it is not a day or a day before a time window    
    else:
        # switch off all devices in the room
        logger.info('We are not in the window logic')
        _switch_off_devices(devices_map, list_OnOffDevices, daemon_config)
        
def _set_logic_priority(logic_time, room, priority):
    # set the value of priority for the logic if there isn't a logic with high priority for the room
    
    # check if there is already a logic for the room
    if ( actual_logic.has_key(room.id) ):
        # check priority of the logic saved for the room
        if ( actual_logic.get(room.id)[1] > priority ):
            logger.info("Update logic for room " + str(room.id) + " where start: " + str(logic_time.start) + " and stop: " + str(logic_time.stop) + " with priority: " + str(priority))
                
            actual_logic.update({ room.id :  ( logic_time , priority )})
                
        else:
            logger.info("There is a logic with higher priority")
    else:
        # there isn't already a logic saved for the room
        logger.info("Save logic for room " + str(room.id) + " where start: " + str(logic_time.start) + " and stop: " + str(logic_time.stop) + " with priority: " + str(priority))

        actual_logic.update({ room.id :  ( logic_time , priority ) })


def _check_priority_logic(logic_time, room, today, window_start, window_stop):
    logger.info("Check priority logic for room: " + str(room.id))
    
    # set next day of week
    if today.weekday() == 6:
        next_day = 0
    else:
        next_day = today.weekday() + 1
    
    # check if today day of week is in the days of logic
    if days[today.weekday()] in logic_time.days:
            
        # check if we are in the time window of the logic
        if today >= window_start and today <= window_stop:
            logger.info('We are in the time window of the logic')
            
            _set_logic_priority(logic_time, room, 1)
            
        # else check if we are before the start window of the logic
        elif today < window_start:
            logger.info('We are before the time window of the logic')
            
            _set_logic_priority(logic_time, room, 2)

        # else we are after the time window of the logic
        else:
            logger.info("We are after the time window of the logic")
         
            # check if next day of the week is in the days of logic   
            if days[today.weekday() + 1] in logic_time.days:
                logger.info("Next day is in the days of logic")
                
                _set_logic_priority(logic_time, room, 3)
        
            else:
                logger.info("Next day isn't in the days of logic")
                
                _set_logic_priority(logic_time, room, 5)
    
    # else check if next day of week is in the days of logic
    elif days[next_day] in logic_time.days:
        logger.info("Next day is in the days of logic")
        
        _set_logic_priority(logic_time, room, 4)

    # else it is not a day or a day before a time window    
    else:
        logger.info("We are not in the window logic and next day isn't in the days of logic")
        
        _set_logic_priority(logic_time, room, 6)
   
        
def _threshold_temperature_regulation(logic, room, devices_map, averageTemp, list_OnOffDevices, daemon_config):
    logger.info("thresholdTemperatureRegulation " + str(logic.id) + ' for room: ' + str(logic.room) + ' where temperature threshold is ' + str(logic.temp.value))

    _check_average_temp_and_threshold(logic.temp.value, room, devices_map, averageTemp, list_OnOffDevices, daemon_config)


def do_logics():
    logger.info("Do logics.... ")
    
    try:
        config.reload()
    
        # read the configuration 
        daemon_config = config.read_daemon_config()
    
        # read the logics from configuration and create convenient map
        logics = config.read_logics()
        logics_map = dict((logic.id, logic) for logic in logics)
    
        # read devices from configuration and create convenient map
        devices = config.read_devices()
        devices_map = dict((device.id, device) for device in devices)
        
        statuses = get_device_status_list(devices, daemon_config)
        status_map = dict((status.id, status) for status in statuses)
    
        # read rooms from configuration and create convenient map
        rooms = config.read_rooms()
        rooms_map = dict((room.id, room) for room in rooms)
        
    except:
        return
    
    # get today date and time
    today = datetime.datetime.now()
    
    logger.info('Date and time: ' + str(days[today.weekday()]) + ' ' + str(today))    
    
    # get average external temperature
    averageExternalTemp = _get_average_external_temp(devices, status_map, daemon_config)
    
    for logic_id in logics_map.keys():
        
        logic = logics_map[logic_id]
        
        # get the room for the logic
        room = rooms_map[logic.room]
        
        # get the average temperature in the room if not yet
        if not temp_status.has_key(room.id):
            _get_average_temperature(room, status_map, daemon_config)
        
        # if logic is enabled
        if logic.enabled == True:
            
            # if there was an error on reading temperature from sensors
            if temp_status.get(room.id) == UNABLE_TO_READ_VALUE:
                logger.info('Error on reading temperature from sensors: switch ON all devices in room ' + str(room.name))
                
                # get the list of status of all OnOff devices in the room
                list_OnOffDevices = _get_onoffdevices_status(room, status_map, daemon_config)

                # check devices off and turn them on
                _switch_on_devices(devices_map, list_OnOffDevices, daemon_config)
            
            # else do logics    
            else:
                if logic.type == 'ThresholdTemperature':
                    # get the list of status of all OnOff devices in the room
                    list_OnOffDevices = _get_onoffdevices_status(room, status_map, daemon_config)

                    _threshold_temperature_regulation(logic, room, devices_map, temp_status.get(room.id), list_OnOffDevices, daemon_config)
                
                elif logic.type == 'TimeProgramming':
                    for logic_time in logic.time:
                        # get the start of the window for the day
                        window_start = datetime.datetime.strptime(str(today.year)+'-'+str(today.month)+'-'+str(today.day)+' '+time.strftime("%H:%M", logic_time.start), '%Y-%m-%d %H:%M')
                        logger.info('Start time ' + str(window_start))
    
                        # get the stop of the window for the day
                        window_stop = datetime.datetime.strptime(str(today.year)+'-'+str(today.month)+'-'+str(today.day)+' '+time.strftime("%H:%M", logic_time.stop), '%Y-%m-%d %H:%M')
                        logger.info('Stop time ' + str(window_stop))
                
                        # check priority for the logic in the room
                        _check_priority_logic(logic_time, room, today, window_start, window_stop)
                
    #for (saved_room_id, saved_logic_id) in actual_logic.items():
    for saved_room_id in actual_logic.keys():
        logger.info('Time Programming Logic with high priority for room ' + str(saved_room_id) + ' is start: ' + str(actual_logic.get(saved_room_id)[0].start) + ' and stop: ' + str(actual_logic.get(saved_room_id)[0].stop))
        
        logic_time = actual_logic.get(saved_room_id)[0]
        
        room = rooms_map[saved_room_id]
        
        # get the list of status of all OnOff devices in the room
        list_OnOffDevices = _get_onoffdevices_status(room, status_map, daemon_config)

        
        _time_programming_regulation(logic_time, room, devices_map, today, temp_status.get(room.id), averageExternalTemp, list_OnOffDevices, daemon_config)
    
    # clear the dictionary of priority logics
    actual_logic.clear()
    
    # update the dictionary of last values
    last_status.clear()
    last_status.update(temp_status)
    
    # clear the dictionary of temperature values
    temp_status.clear()
