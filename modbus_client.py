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
from pymodbus.client.sync import ModbusTcpClient, ConnectionException
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder

import logging

from exception import ConnectionExceptionRest

#---------------------------------------------------------------------------#
# configure the service loggerging
#---------------------------------------------------------------------------#
logger = logging.getLogger(__name__)

def open_client(address, port):
    logger.debug("open connection to " + str(address))
    return ModbusTcpClient(address, port)

def close_client(client):
    return client.close()

def read_register(client, register):    
    logger.info("---- Read register " + str(register))

    try:
        rr = client.read_holding_registers(register, count=2, unit=1)
        logger.info("Register value are " + str(rr.registers))
        
        # build register
        reg=[0, 0]
        reg[0] = rr.registers[0]
        reg[1] = rr.registers[1]
    
        # decode register 
        decoder = BinaryPayloadDecoder.fromRegisters(reg, endian=Endian.Big)
        decoded = decoder.decode_32bit_float()
        
        logger.info("Register decoded value are " + str(decoded))
        return decoded
    except ConnectionException:
        raise ConnectionExceptionRest("")

def read_coil(client, coil):    
    logger.info("---- Read coil " + str(coil))
    
    try:
        result = client.read_coils(coil, count=1)
        
        if result == None:
            raise ConnectionExceptionRest("") 
        
        logger.info("Status coil: " + str(result.bits[0]))
    
        return result.bits[0]
    except ConnectionException:
        raise ConnectionExceptionRest("")

def write_coil(client, coil, value):        
    logger.info("---- Write coil " + str(coil) + " Value: " + str(value))

    try:        
        client.write_coil(coil, value)
    except ConnectionException:
        raise ConnectionExceptionRest("")
    
def read_input_registers(client, register):    
    logger.info("---- Read register " + str(register))
    
    result = client.read_input_registers(register, count=1)
    
    logger.info("Input register: " + str(result.registers))

    return result.registers[0]
