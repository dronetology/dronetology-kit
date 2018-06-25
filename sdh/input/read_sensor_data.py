#!/usr/bin/env python
import time
import serial
import logging
import sys


logging.basicConfig(format='%(asctime)s %(message)s', filename='dronetology.log',level=logging.DEBUG)


# 3rd party modules
import posix_ipc

SERIAL_CONNECTION_STRING="/dev/ttyUSB0"

print 'DATA SOURCE MANAGER:Serial port init................'
logging.debug( 'DATA SOURCE MANAGER:Serial port init...........')

try_connection=True

while try_connection:
    try:
        ser = serial.Serial(
        port=SERIAL_CONNECTION_STRING,
        baudrate = 38400,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=1
        )
        logging.debug("DATA SOURCE MANAGER:.......Serial Port opened...") 
        print("DATA SOURCE MANAGER:.......Serial Port opened...") 
        try_connection=False

    except:
        print 'DATA SOURCE MANAGER:Serial port error.....exit'
        logging.error( 'DATA SOURCE MANAGER:Serial port error....exit')
        time.sleep(3)
        logging.error( 'DATA SOURCE MANAGER: try connection again.........')
        print ('DATA SOURCE MANAGER: try connection again.........')


 
harvested_sensors=[]

# Create the message queue.
try:
    mq = posix_ipc.MessageQueue("/INPUT_QUEUE", posix_ipc.O_CREX)
except posix_ipc.ExistentialError:
    mq = posix_ipc.MessageQueue("/INPUT_QUEUE")


print("DATA SOURCE MANAGER: waiting for a conection to a sensor ........")
logging.debug("DATA SOURCE MANAGER: waiting for a conection to a sensor ........")

while 1:
    x=ser.readline()
    a=x.find("SENSOR ID:")
    b=x.find("END")

    #..............last sensor .....SENSOR ID:562............
    sensor= x[a:b]
    if(a>-1 and b>-1):
        #no se loguea info de recopilacion pq hay que conectarse al vehiculo y hay ya telemetria cada sg
        #mavlink.log_vehicle_status("...connected to sensor "+sensor)
        if(sensor in harvested_sensors):
            logging.debug("DATA SOURCE MANAGER: Sensor already harvested "+sensor)
            print("DATA SOURCE MANAGER: Sensor already harvested "+sensor)
        else:
            logging.debug("DATA SOURCE MANAGER:Sent to queue, not harvested "+sensor)
            print("DATA SOURCE MANAGER:Sent to queue, not harvested "+sensor)
            harvested_sensors.append(sensor)
            mq.send(sensor)
