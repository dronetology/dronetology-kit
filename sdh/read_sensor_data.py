#!/usr/bin/env python
import time
import serial
import logging
import sys
import exceptions


logging.basicConfig(format='%(asctime)s %(message)s', filename='./log/dronetology.log',level=logging.DEBUG)


# 3rd party modules
import posix_ipc

SERIAL_CONNECTION_STRING="/dev/ttyUSB0"


def signal_handler(signal, frame):
    print('DATA SOURCE MANAGER: You pressed Ctrl+C!')
    logging.debug('DATA SOURCE MANAGER: You pressed Ctrl+C!')

    if ser is None:
        print('Serial connection is None')
    else:
        ser.close()

    sys.exit(0)

def repeated_connection():
    
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

        except exceptions as other_error:
            #print 'DATA SOURCE MANAGER:Serial port error.....exit'
            #logging.error( 'DATA SOURCE MANAGER:Serial port error....exit')
            time.sleep(5)
            logging.error( 'DATA SOURCE MANAGER: try connection again.........')
            print ('DATA SOURCE MANAGER: try connection again.........')
    
    return ser


 
harvested_sensors=[]

# Create the message queue.
try:
    mq = posix_ipc.MessageQueue("/INPUT_QUEUE", posix_ipc.O_CREX)
except posix_ipc.ExistentialError:
    mq = posix_ipc.MessageQueue("/INPUT_QUEUE")

serial_connection = repeated_connection()
print("DATA SOURCE MANAGER: waiting for a sensor connection........")
logging.debug("DATA SOURCE MANAGER: waiting for a sensor connection........")

while 1:

    x=serial_connection.readline()

    a=x.find("SENSOR ID:")
    b=x.find("END")

    aa=x.find("RSSI:")
    bb=x.find("END-RSSI")

    #print x

    #..............last sensor .....SENSOR ID:562............
    sensor= x[a:b].strip()
    rssi_received= x[aa:bb].strip()

   
    if(a>-1 and b>-1 and sensor):
        #no se loguea info de recopilacion pq hay que conectarse al vehiculo y hay ya telemetria cada sg
        #mavlink.log_vehicle_status("...connected to sensor "+sensor)
        serial_connection.close()

        if(sensor in harvested_sensors):
            logging.debug("DATA SOURCE MANAGER: Sensor already harvested "+sensor)
            print("DATA SOURCE MANAGER: Sensor already harvested "+sensor)
        else:
            logging.debug("DATA SOURCE MANAGER: Sending sensor to queue, not harvested "+sensor)
            print("DATA SOURCE MANAGER: Sending sensor to queue, not harvested "+sensor)
            harvested_sensors.append(sensor)
            mq.send(sensor)
        
        serial_connection = repeated_connection()

    if(aa>-1 and bb>-1 and rssi_received):
        logging.debug("DATA SOURCE MANAGER: "+rssi_received)
        print("DATA SOURCE MANAGER: "+rssi_received)
    
    x=""
    sensor=""
    rssi_received=""

