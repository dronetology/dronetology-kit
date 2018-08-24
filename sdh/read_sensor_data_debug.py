#!/usr/bin/env python
import time
import serial
import logging
import sys
import exceptions
import random
import math

# Import DroneKit-Python
from dronekit import LocationGlobalRelative

from xml.etree.ElementTree import SubElement, Element, tostring

import xml.etree.ElementTree as ET

logging.basicConfig(format='%(asctime)s %(message)s', filename='./log/dronetology.log',level=logging.DEBUG)


# 3rd party modules
import posix_ipc

import imp
sensor = imp.load_source('sensor', './util/sensor.py')
util = imp.load_source('util', './util/util.py')


def signal_handler(signal, frame):
    print('DATA SOURCE MANAGER: You pressed Ctrl+C!')
    logging.debug('DATA SOURCE MANAGER: You pressed Ctrl+C!')

    sys.exit(0)


# Create the message queue.
try:
    mq = posix_ipc.MessageQueue("/INPUT_QUEUE", posix_ipc.O_CREX)
except posix_ipc.ExistentialError:
    mq = posix_ipc.MessageQueue("/INPUT_QUEUE")

try:     
    mqp = posix_ipc.MessageQueue("/UAS_POSITION", posix_ipc.O_CREX)  
except posix_ipc.ExistentialError:   
    mqp = posix_ipc.MessageQueue("/UAS_POSITION")

try:     
    mqs = posix_ipc.MessageQueue("/FLIGHT_TYPE_QUEUE")  
except posix_ipc.ExistentialError:   
    mqs = posix_ipc.MessageQueue("/FLIGHT_TYPE_QUEUE")


"""
tree = ET.parse('./dronetology/init/isa1-wsn1-data.rdf')

ns = {'owl': 'http://www.w3.org/2002/07/owl#',
      'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
      }

sensor=tree.find('.//owl:NamedIndividual[@rdf:about="http://www.dronetology.net/dronetology-sdh.owl#sensor_1"]', ns)


for child in sensor:
    if(child.tag.find("hasLatitude")>-1):
        #print child.text
        lat=child.text
    elif (child.tag.find("hasLongitude")>-1):
        #print child.text
        lon=child.text
    else:
        print child.tag, child.attrib, child.text
    
#LocationGlobalRelative(lat, lon, SENSOR_ALTITUDE)
"""


#blocked until receive flight type..........................................
print 'DATA SOURCE MANAGER:waiting for flight_type...............'
logging.debug( 'DATA SOURCE MANAGER: waiting for flight_type............')
flight_params= mqs.receive()[0] 
#para evitar que se quede vacia
mqs.send(flight_params)

print('DATA SOURCE MANAGER: ............waiting for sensor harvesting................')
#time.sleep(20)

harvested_sensors=[]

sensors_locations=sensor.sensors_locations(flight_params)

harvested_sensors=[]
point=[]

while len(harvested_sensors)<4:

    while mqp.current_messages>1:
        s= mqp.receive(1)[0]
        #print "UAS position discarded: ..........."+s

    try:
        s= mqp.receive(1)[0]
        print "UAS position ..........."+s
        point=s.split(",")
        
        for s_position in sensors_locations:
            if point is None:
                print "........................no position to check sensors.................."
            else:            
                sensor_distance=util.get_distance_metres_3d(s_position, LocationGlobalRelative(float(point[0]), float(point[1]), 15))
                if( (sensor_distance-random.randint(1, 15))<30):                    
                    sensor=sensors_locations.index(s_position)+1
                    if(sensor in harvested_sensors):                        
                        print("DATA SOURCE MANAGER: Sensor already harvested "+str(sensor))
                    else:
                        harvested_sensors.append(sensor)       
                        mq.send(str(sensor))
                        print("DATA SOURCE MANAGER: ................harvested sensor "+str(sensor)+"......pending sensors :"+str(4-len(harvested_sensors)))
             

    except posix_ipc.BusyError: 
        print "................no position............"

    """
    if(random.randint(1, 10)>9):
        sensor=random.randint(1, 4) 
        if(sensor in harvested_sensors):
            #print("DATA SOURCE MANAGER: Sensor already harvested "+str(sensor))
            print ""
        else:
            harvested_sensors.append(sensor)
            print("DATA SOURCE MANAGER: ................harvested sensor "+str(sensor)+"......pending sensors :"+str(4-len(harvested_sensors)))            
            mq.send(str(sensor))
    """     
    
    time.sleep(1)


print("DATA SOURCE MANAGER:..................ALL SENSORS HARVESTED.............................. ")    
logging.debug("DATA SOURCE MANAGER: ENDED  ")  


while mqp.current_messages>1:
    s= mqp.receive(1)[0]
    print "....continue discarding UAS positions ..........."+s
    time.sleep(1)


#sys.exit(0)
