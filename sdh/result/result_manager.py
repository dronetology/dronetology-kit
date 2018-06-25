#!/usr/bin/env python
import time
import subprocess
import math
import re
import logging
import exceptions
import dronekit
import sys
import signal


logging.basicConfig(format='%(asctime)s %(message)s', filename='dronetology.log',level=logging.DEBUG)


# 3rd party modules
import posix_ipc

# Import DroneKit-Python
from dronekit import connect, VehicleMode, LocationGlobalRelative

import imp
mavlink = imp.load_source('mavlink', './result/mavlink/mavlink.py')


########### constantes ######################

#............42.8305481,-1.730324.......home position for distance control 
HOME_LOCATION = LocationGlobalRelative(42.8305481, -1.730344, 20)

#DSF: debe estar cerca de HOME, hasta que se calcule un nuevo centroide
#ISA1: debe ser W3
W1_LOCATION = LocationGlobalRelative(42.8305481, -1.730324, 20)

VEHICLE_VELOCITY=2

HOME_ALTITUDE=10
TARGET_ALTITUDE=10

SECURITY_DISTANCE=200
MINIMUN_DISTANCE=10


start_time=time.time()

##############################################

def signal_handler(signal, frame):
    print('RESULT MANAGER: You pressed Ctrl+C!')
    logging.debug('RESULT MANAGER: You pressed Ctrl+C!')

    if vehicle is None:
        print('Vehicle is None')
    else:
        vehicle.close()

    sys.exit(0)


def get_distance_metres(aLocation1, aLocation2):
    """
    Returns the ground distance in metres between two LocationGlobal objects.

    This method is an approximation, and will not be accurate over large distances and close to the 
    earth's poles. It comes from the ArduPilot test code: 
    https://github.com/diydrones/ardupilot/blob/master/Tools/autotest/common.py
    """
    dlat = aLocation2.lat - aLocation1.lat
    dlong = aLocation2.lon - aLocation1.lon
    return math.sqrt((dlat*dlat) + (dlong*dlong)) * 1.113195e5


# the message queue.
# mq = posix_ipc.MessageQueue("/RESULT_QUEUE")

#................................................................
# for testing....................................................
# Create the message queue.
try:
    mq = posix_ipc.MessageQueue("/RESULT_QUEUE", posix_ipc.O_CREX)    
except posix_ipc.ExistentialError:
    mq = posix_ipc.MessageQueue("/RESULT_QUEUE")
#................................................................
#................................................................
#mq.send("NEW_CENTROID||34.0|-43.0")

print 'RESULT MANAGER: starting ...............'
logging.debug( 'RESULT MANAGER: starting ............')

signal.signal(signal.SIGINT, signal_handler)

#para parar el procesado si ya se ha enviado un RTL
continue_processing=True

vehicle=mavlink.repeated_connection()

print "RESULT MANAGER: connected to vehicle"
logging.debug ("RESULT MANAGER : connected to vehicle")

#####################################################################
#####################################################################
################ move drone to a point
distance_to_init_point=get_distance_metres(HOME_LOCATION, W1_LOCATION)
mavlink.set_home_position(vehicle, HOME_ALTITUDE)
mavlink.arm_and_takeoff(vehicle, TARGET_ALTITUDE)
vehicle.airspeed = VEHICLE_VELOCITY

#esta posicion sirve para ISA1 y DSF
vehicle.simple_goto(W1_LOCATION)

print "RESULT MANAGER: moving to W1_LOCATION"
logging.debug("RESULT MANAGER: moving to W1_LOCATION")

## puede esperar aqui o en el receive
time.wait(int(round(distance_to_init_point/VEHICLE_VELOCITY)))

loop=1

while 1:

    logging.debug("RESULT MANAGER: waiting for inference result .................")
    print("RESULT MANAGER: waiting for inference result...............") 
    ##if too long ???...............   
    try:
        s= mq.receive(1)[0]
        logging.debug("RESULT MANAGER: received inference result :"+s)
        print("RESULT MANAGER: received inference result :"+s)  
        mavlink.log_vehicle_status(vehicle, "....received inference..", start_time)   
    except posix_ipc.BusyError: 
        logging.debug("RESULT MANAGER: queue empty ")
        print("RESULT MANAGER: queue empty ") 
        s="noInferenceResult"
        mavlink.log_vehicle_status(vehicle, "....TELEMETRY..", start_time) 
       
    if(s.find("AVOID_NEXT_WAYPOINT")>-1):   
        pattern = r'[-+]?\d+\.\d+'
        m = re.findall(pattern, s)

        print "RESULT MANAGER: ISA1 AVOID NEXT_WAYPOINT, changed course to ......."+m
        logging.debug ("RESULT MANAGER: ISA1 AVOID NEXT_WAYPOINT, changed course to ..........."+m)  

        pattern = r'[-+]?\d+\.\d+'
        m = re.findall(pattern, s)

        print "RESULT MANAGER: AVOID_NEXT_WAYPOINT flight to ......."+m
        logging.debug ("RESULT MANAGER: AVOID_NEXT_WAYPOINT flight to ..........."+m)  

        waypoint_togo = LocationGlobalRelative(float(m[0]), float(m[1]), TARGET_ALTITUDE)      

        #.................hay condiciones previas: ya esta en vuelo hacia W1....                
        #.................vehicle.simple_goto(waypoint_togo)
        nextwaypoint=vehicle.commands.next
        vehicle.commands.next =  nextwaypoint+1  
        mavlink.log_vehicle_status(vehicle, "....AVOID_NEXT_WAYPOINT...", start_time)       

        
    if(s.find("DELETE_WAYPOINT")>-1): 
        #no llega pq no es necesario interaccion con el vehiculo         
        print "RESULT MANAGER: DELETE_WAYPOINT Deleting waypoint........."+s
        logging.debug ("RESULT MANAGER: DELETE_WAYPOINT Deleting waypoint............."+s)  
        vehicle.close() 
        break 

        
    if(s.find("NEW_CENTROID")>-1):       
        pattern = r'[-+]?\d+\.\d+'
        m = re.findall(pattern, s)

        print "RESULT MANAGER: NEW_CENTROID ......."+m
        logging.debug ("RESULT MANAGER: NEW_CENTROID ..........."+m)  

        new_centroid = LocationGlobalRelative(float(m[0]), float(m[1]), TARGET_ALTITUDE)

        #control distancia con la ubicacion de HOME
        if(get_distance_metres(HOME_LOCATION, new_centroid)>SECURITY_DISTANCE):            
            print "RESULT MANAGER: ERROR new_centroid far away....."+m
            logging.error ("RESULT MANAGER: ERROR new_centroid far away.........."+m)  

        else:
            print "RESULT MANAGER: move to centroid...."+m
            logging.debug ("RESULT MANAGER: move to centroid........"+m)             
            
            mavlink.log_vehicle_status(vehicle, "....NEW_CENTROID..", start_time)   

            distance_to_new_centroid=get_distance_metres(vehicle.location.global_frame, new_centroid)

            if(distance_to_new_centroid<MINIMUN_DISTANCE):
                print "RESULT MANAGER: same centroid ...."+m
                logging.info ("RESULT MANAGER: same centroid ........"+m) 
            elif(distance_to_new_centroid>SECURITY_DISTANCE):
                print "RESULT MANAGER: centroid far away...."+m
                logging.info ("RESULT MANAGER: centroid far away........"+m)             
            else:
                #.................hay condiciones previas: ya esta en vuelo hacia W1....                
                vehicle.simple_goto(new_centroid)
                #################################################################
                #wait until arrives.....??? if finished before ???
                print "RESULT MANAGER: waiting until arrives to centroid ...."+m
                logging.info ("RESULT MANAGER: waiting until arrives to centroid ........"+m) 
                time.wait(int(round(distance_to_new_centroid/VEHICLE_VELOCITY)))

                while(get_distance_metres(vehicle.location.global_frame, new_centroid)>MINIMUN_DISTANCE):
                    time.wait(1)

                print "RESULT MANAGER: Arrived to centroid ...."+m
                logging.info ("RESULT MANAGER: Arrived to centroid ........"+m)        
        

    if(s.find("END_DSF")>-1):
        print "RESULT MANAGER: END_DSF Returning to Launch...."+s
        logging.debug ("RESULT MANAGER: END_DSF Returning to Launch ........"+s)       
        if(continue_processing):            
            mavlink.log_vehicle_status(vehicle, "....END_DSF.....", start_time)                    
            mavlink.set_RTL_mode(vehicle)
            vehicle.close()
            continue_processing=false   

    if(s.find("END_ISA1")>-1):
        print "RESULT MANAGER: END_ISA1 Returning to Launch...."+s
        logging.debug ("RESULT MANAGER: END_ISA1 Returning to Launch ........"+s)       
        if(continue_processing):            
            mavlink.log_vehicle_status(vehicle, "....END_ISA1.....", start_time)                    
            mavlink.set_RTL_mode(vehicle)
            vehicle.close()
            continue_processing=false            
              
    loop += 1
    print("RESULT MANAGER: "+loop+" Completed processing "+s)    
    logging.debug("RESULT MANAGER: "+loop+" Completed processing "+s)  
    
    time.sleep(1)

print("RESULT MANAGER: processing ENDED  ")    
logging.debug("RESULT MANAGER: processing ENDED  ")  
