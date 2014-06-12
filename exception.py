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
# -*- coding: utf-8 -*-


class RestException(Exception):
    def __init__( self, code, message ):
        self.code = code
        Exception.__init__(self, message)

    def to_json(self):
        return {"error" : { "code" : self.code, "message" : str(self) }}

class MissingParamException(RestException):
    def __init__( self, param ):
        RestException.__init__(self, 1, 'Missing param exception: missing %s' % param)
                
class InvalidParamException(RestException):
    def __init__( self, param ):
        RestException.__init__(self, 3, 'Invalid param exception: invalid %s' % param)
        
class ElementUsedException(RestException):
    def __init__( self, param ):
        RestException.__init__(self, 4, 'Element used exception exception: used by %s' % param)
                
class ElementNotFoundException(RestException):
    def __init__(self):
        RestException.__init__(self, 0, 'Element not found exception: invalid id')
        
class ConnectionExceptionRest(RestException):
    def __init__( self, param ):
        RestException.__init__(self, 5, 'Unable to connect to modbus  gateway')                
        
class LogicTypeAlreadyPresentException(RestException):
    def __init__( self, param ):
        RestException.__init__(self, 6, 'Logic already present exception: on logic type %s' % param)
                
class InvalidExternalDeviceException(RestException):
    def __init__( self):
        RestException.__init__(self, 7, 'Invalid external device: the room must have only external device type or not')
        
class TimeProgrammingOverlapException(RestException):
    def __init__( self):
        RestException.__init__(self, 8, 'time program overlap exception')
        
class PermissionDeniedException(RestException):
    def __init__( self):
        RestException.__init__(self, 9, 'permission denied')
                
