# Application 

The application is divided into two part rest api and services.

The rest api is a bottle application and can started with the python script 
* restdev.py - start the api using the internal server of bottle 
* restwsgi.py - wsgi version of script (tested on lighttpd)

Note: the restwsgi.py must be mapped to http://<ip_address>/api

The service supported are:
* alert - simple alerting based on room temperature and measure error
* logics - simple service for thermo regulation of room (time based and temperature based)

The service can be started on command line with [SERVICENAME]command.py or using daemon version [SERVICENAME]daemon.py, (the start script are in init.d directory)

The conf directory contains configuration file for myna and logging.

## Requirements 

* Raspbian
* lighttpd
* python 2.7 

## Libraries 

The application uses the following libraries

* python-pymodbus 1.2 https://github.com/bashwork/pymodbus
* python-daemon 1.5.5 https://pypi.python.org/pypi/python-daemon/
* python-bottle 0.10.11 http://bottlepy.org/