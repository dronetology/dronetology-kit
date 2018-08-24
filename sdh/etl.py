#!/usr/bin/env python
import time
import re
import logging


logging.basicConfig(format='%(asctime)s %(message)s', filename='./log/dronetology.log',level=logging.DEBUG)


# 3rd party modules
import posix_ipc

import imp
util = imp.load_source('util', './util/util.py')


# ..............for testing purposes
# Create the message queue.
try:
    mq = posix_ipc.MessageQueue("/INPUT_QUEUE", posix_ipc.O_CREX)    

except posix_ipc.ExistentialError:
    mq = posix_ipc.MessageQueue("/INPUT_QUEUE")


try:     
    mqs = posix_ipc.MessageQueue("/FLIGHT_TYPE_QUEUE", posix_ipc.O_CREX)  
except posix_ipc.ExistentialError:   
    mqs = posix_ipc.MessageQueue("/FLIGHT_TYPE_QUEUE")


#blocked until receive flight type
flight_params= mqs.receive()[0] 
#para evitar que se quede vacia
mqs.send(flight_params)

logging.debug("ETL MODULE: flight params................."+flight_params)
print("ETL MODULE: flight params.............."+flight_params) 


print("ETL MODULE: waiting for a new harvested sensor ........")
logging.debug("ETL MODULE: waiting for a new harvested sensor .........")


harvested_sensors=0

while 1:

    #print("ETL MODULE: waiting for a new harvested sensor ........")
    #logging.debug("ETL MODULE: waiting for a new harvested sensor .........")

    try:
        s= mq.receive(2)[0]  
        logging.debug("ETL MODULE:Received from queue, new sensor harvested ................."+s)
        #print("ETL MODULE:Received from queue, new sensor harvested .............."+s)
    except posix_ipc.BusyError: 
        #logging.debug("ETL MODULE: queue empty ")
        #print("ETL MODULE: queue empty ")   
        s="noSensorHarvested" 

    pattern = r'\d+'
    m = re.findall(pattern, s)    

    if not m:
        logging.debug("ETL MODULE: no sensor harvested ")
        #print("ETL MODULE: no sensor harvested ")
    else:
        sensor_id=int(m[0])
        harvested_sensors=harvested_sensors+1
        util.addHarvestedSensor(flight_params, sensor_id)            
        print("ETL MODULE: ............sensor added to RDF........"+m[0]+".............pending sensors:"+str(4-harvested_sensors))
        logging.debug("ETL MODULE: harvested sensor added to RDF......"+m[0])               
        
            
    time.sleep(1)