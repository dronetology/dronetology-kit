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
import os

logging.basicConfig(format='%(asctime)s %(message)s', filename='./log/dronetology.log',level=logging.DEBUG)


# 3rd party modules
import posix_ipc

# Import DroneKit-Python
from dronekit import connect, VehicleMode, LocationGlobalRelative

import imp

mavlink = imp.load_source('mavlink', './mavlink/mavlink.py')
inference = imp.load_source('inference', './inference/inference.py')
util = imp.load_source('util', './util/util.py')

MAX_SECURITY_LOOP=180
SECURITY_DISTANCE=400
MINIMUN_DISTANCE=10

##############################################


# Create the message queue.
try:
    mq = posix_ipc.MessageQueue("/RESULT_QUEUE", posix_ipc.O_CREX)   
except posix_ipc.ExistentialError:
    mq = posix_ipc.MessageQueue("/RESULT_QUEUE")
   
try:     
    mqw = posix_ipc.MessageQueue("/MISSION_WAYPOINT_QUEUE", posix_ipc.O_CREX)      
except posix_ipc.ExistentialError:    
    mqw = posix_ipc.MessageQueue("/MISSION_WAYPOINT_QUEUE")  
    
try:     
    mqs = posix_ipc.MessageQueue("/FLIGHT_TYPE_QUEUE")  
except posix_ipc.ExistentialError:   
    mqs = posix_ipc.MessageQueue("/FLIGHT_TYPE_QUEUE")

try:     
    mqp = posix_ipc.MessageQueue("/UAS_POSITION", posix_ipc.O_CREX)  
except posix_ipc.ExistentialError:   
    mqp = posix_ipc.MessageQueue("/UAS_POSITION")


#############################...................................


print 'RESULT MANAGER: starting ...............'
logging.debug( 'RESULT MANAGER: starting ............')

flight_distance=[0]
start_time=time.time()

signal.signal(signal.SIGINT, util.signal_handler)


#blocked until receive flight type..........................................
print 'RESULT MANAGER: waiting for flight_type...............'
logging.debug( 'RESULT MANAGER: waiting for flight_type............')
flight_params= mqs.receive()[0] 
#para evitar que se quede vacia
mqs.send(flight_params)

logging.debug("RESULT MANAGER: flight type................."+flight_params)
print("RESULT MANAGER: flight type.............."+flight_params) 


###################################################

vehicle=mavlink.repeated_connection(flight_params)

print "RESULT MANAGER: connected to vehicle"
logging.debug ("RESULT MANAGER : connected to vehicle")

###########################
"""
@vehicle.on_attribute('last_heartbeat')   
def listener(self, attr_name, value):
    # `attr_name` is the observed attribute (used if callback is used for multiple attributes)
    # `attr_name` - the observed attribute (used if callback is used for multiple attributes)
    # `value` is the updated attribute value.
    print "HEART ATTR: %s changed to: %s" % (attr_name, value)

    vehicle=mavlink.repeated_connection("drone|psa|1")
    mavlink.set_RTL_mode(vehicle)

    while True:
        stop_distance = mavlink.distance_UAS_to_home(vehicle)
        print " altitude: ", vehicle.location.global_relative_frame.alt 
        #Break and return from function just below target altitude. 
        print " distance to home : ", stop_distance  

        if (vehicle.location.global_relative_frame.alt<0.2 and stop_distance<MINIMUN_DISTANCE): 
            print "Reached home position & altitude............."
            break

    time.sleep(1)  
"""
###################################

mavlink.init_flight(flight_params, vehicle)

loop=1

#dsf centroide que bloquea
flight_blocked=0

nextwaypoint_sent="undefined"

############## has altitude....................as relative for telemetry
previous_position=mavlink.get_home_position(vehicle)
previous_position.alt=0

sensors_visited=[]

while 1:

    previous_position= mavlink.log_vehicle_status(vehicle, "...TELEMETRY....", previous_position, start_time, flight_distance)  

    #also needed in whiles
    try:
        mqp.send(str(previous_position.lat)+","+str(previous_position.lon),1)
    except posix_ipc.BusyError: 
        print("....................timeout sending position........")

    nextwaypoint=vehicle.commands.next
    logging.debug("RESULT MANAGER:  flying to..........."+str(nextwaypoint))
    print("RESULT MANAGER:  flying to............. "+str(nextwaypoint))

    #mavlink.read_channels(vehicle)

    try:
        #print "RESULT MANAGER: ................queue size............."+str(mq.current_messages)

        while mq.current_messages>1 and flight_params.find("dsf")>-1:
            s= mq.receive(1)[0]
            print "RESULT MANAGER: ..........discarding inference........................"+s

        s= mq.receive(1)[0]
        logging.debug("RESULT MANAGER: received inference result :"+s)
        print("RESULT MANAGER: .....................received inference result ...........:"+s)  
        previous_position=mavlink.log_vehicle_status(vehicle, "....received inference..", previous_position, start_time, flight_distance) 

    except posix_ipc.BusyError: 
        logging.debug("RESULT MANAGER: queue empty ")
        print("RESULT MANAGER: .....................inference queue empty..........") 
        s="noInferenceResult"
        mavlink.log_vehicle_status(vehicle, "....TELEMETRY..", previous_position, start_time, flight_distance) 

    #............................................................................................
    #.................................the security stop condition...............................
    #...........................................................................................
    stop_distance = mavlink.distance_UAS_to_home(vehicle)

    if(loop==MAX_SECURITY_LOOP):         
        logging.debug("RESULT MANAGER:  MAX_SECURITY_LOOP reached flight plan finished......"+str(nextwaypoint))
        print("RESULT MANAGER:  MAX_SECURITY_LOOP reached flight plan finished..... "+str(nextwaypoint))        
        break      
    else:
        if((flight_params.find("psa")>-1) and (nextwaypoint>=3) and (stop_distance<MINIMUN_DISTANCE)):
            logging.debug("RESULT MANAGER: PSA finish................")
            print("RESULT MANAGER: .........................PSA finish................... ")    
            break

        elif ((flight_params.find("bfa")>-1) and (nextwaypoint>=3) and (stop_distance<MINIMUN_DISTANCE)):
            logging.debug("RESULT MANAGER: BFA finish......")
            print("RESULT MANAGER: .........................BFA finish.......... ")    
            break

        elif( flight_params.find("isa1")>-1):
            if nextwaypoint_sent==str(nextwaypoint):
                print "..................ALREADY sent next waypoint..................."
            else:
                print "..................SENDING next waypoint..................."+str(nextwaypoint)
                nextwaypoint_sent=str(nextwaypoint)   
                mqw.send(str(nextwaypoint)) 

            if( (nextwaypoint>=3) and (stop_distance<MINIMUN_DISTANCE) ):
                logging.debug("RESULT MANAGER: ISA1 finish......")
                print("RESULT MANAGER: .........................ISA1 finish.......... ")    
                break

        elif (flight_params.find("dsf")>-1 and s=="noInferenceResult"):

            pending_sensor_position=inference.pending_sensor_latlon(flight_params, sensors_visited)  
            
            if( vehicle.mode.name=='AUTO' and pending_sensor_position!= None):   

                print "RESULT MANAGER: .................DSF GOTO sensors.............................. "

                distance_to_pending_sensor=util.get_distance_metres(vehicle.location.global_frame, pending_sensor_position)

                vehicle.mode = VehicleMode("GUIDED")
                while not vehicle.mode.name=='GUIDED':  #Wait until mode has changed
                    print " Waiting for GUIDED mode  ..."
                    time.sleep(1)

                vehicle.simple_goto(pending_sensor_position)
                while distance_to_pending_sensor>MINIMUN_DISTANCE:
                    time.sleep(1)
                    previous_position= mavlink.log_vehicle_status(vehicle, "...TELEMETRY....", previous_position, start_time, flight_distance) 
                    try:
                        mqp.send(str(previous_position.lat)+","+str(previous_position.lon),1)
                    except posix_ipc.BusyError: 
                        print("....................timeout sending position........")
                    distance_to_pending_sensor=util.get_distance_metres(vehicle.location.global_frame, pending_sensor_position)

                print "RESULT MANAGER: .............DSF GOTO sensors FINISHED.............................. "

                vehicle.mode = VehicleMode("AUTO")
                while not vehicle.mode.name=='AUTO':  #Wait until mode has changed
                    print " Waiting for AUTO mode  ..."                 
                    time.sleep(1)

            elif(pending_sensor_position == None ):
                logging.debug("RESULT MANAGER: DSF finish...........No sensors pending .......")
                vehicle.commands.next =3
                nextwaypoint=3
            

            if( (nextwaypoint>=3) and (stop_distance<MINIMUN_DISTANCE)):
                logging.debug("RESULT MANAGER: DSF finish......")
                print("RESULT MANAGER: .........................DSF finish.......... ")                  
                break
            


    #............................................................................................
    #.................................the dronetology stop condition...............................
    #........................................................................................... 
    if(s.find("END_DSF")>-1 ):
        print "RESULT MANAGER: END_DSF Returning to Launch.............stop_distance:"+str(stop_distance)
        logging.debug ("RESULT MANAGER: END_DSF Returning to Launch ........stop_distance:"+str(stop_distance))                 
        previous_position=mavlink.log_vehicle_status(vehicle, "....END_DSF.....", previous_position, start_time, flight_distance)  
        if(nextwaypoint==3 and stop_distance<MINIMUN_DISTANCE):
            break
        else:     
            vehicle.commands.next =3
            nextwaypoint=3        
         

    if(s.find("END_ISA1")>-1 ):
        print "RESULT MANAGER: END_ISA1 .............stop_distance:"+str(stop_distance)
        logging.debug ("RESULT MANAGER: END_ISA1 Returning to Launch ........stop_distance:"+str(stop_distance))                  
        previous_position=mavlink.log_vehicle_status(vehicle, "....END_ISA1.....", previous_position, start_time, flight_distance)   
        if(nextwaypoint==4 and stop_distance<MINIMUN_DISTANCE):
            break
        else:     
            vehicle.commands.next =4 
            nextwaypoint=4    
         
    #............................................................................................    
    #...........................................................................................

    if( s.find("AVOID_NEXT_WAYPOINT")>-1):  
                
        pattern = r'[-+]?\d+\.\d+'
        m = re.findall(pattern, s)

        #print "RESULT MANAGER: AVOID_NEXT_WAYPOINT, flight to ......."+s
        #logging.debug ("RESULT MANAGER: AVOID_NEXT_WAYPOINT, flight to ..........."+s)  
        previous_position=mavlink.log_vehicle_status(vehicle, "....AVOID_NEXT_WAYPOINT...", previous_position, start_time, flight_distance) 

        print "RESULT MANAGER: AVOID_NEXT_WAYPOINT, avoid "+str(nextwaypoint)+" ...change to..."+str(nextwaypoint+1)
        logging.debug ("RESULT MANAGER: AVOID_NEXT_WAYPOINT, avoid "+str(nextwaypoint)+" ...change to..."+str(nextwaypoint+1))
        
        print "RESULT MANAGER: AVOID_NEXT_WAYPOINT DEBUG...................changed to next ................."
        vehicle.commands.next =  nextwaypoint+1                       
        nextwaypoint = nextwaypoint+1 
        
    if(s.find("DELETE_WAYPOINT")>-1): 
        #no llega pq no es necesario interaccion con el vehiculo         
        print "RESULT MANAGER: DELETE_WAYPOINT Deleting waypoint........."+s
        logging.debug ("RESULT MANAGER: DELETE_WAYPOINT Deleting waypoint............."+s)        
        

        
    if(s.find("NEW_CENTROID")>-1):       
        pattern = r'[-+]?\d+\.\d+'
        m = re.findall(pattern, s)

        #print "RESULT MANAGER: NEW_CENTROID ......."+s
        logging.debug ("RESULT MANAGER: NEW_CENTROID ..........."+s)  

        new_centroid = mavlink.generate_point(flight_params, m)

        #control distancia con la ubicacion de HOME
        if(mavlink.distance_to_home(vehicle, new_centroid)>SECURITY_DISTANCE):            
            print "RESULT MANAGER: .................ERROR new_centroid far away....."+s
            logging.error ("RESULT MANAGER: ERROR new_centroid far away.........."+s) 
            previous_position=mavlink.log_vehicle_status(vehicle, "....NEW_CENTROID far away..", previous_position, start_time, flight_distance)           
            #sigue el bucle para tener telemetria
            #continue_processing=False   

        else:
            print "RESULT MANAGER: .................move to centroid......."+s
            logging.debug ("RESULT MANAGER: move to centroid........"+s)             
            
            previous_position=mavlink.log_vehicle_status(vehicle, "....NEW_CENTROID..", previous_position, start_time, flight_distance) 

            distance_to_new_centroid=util.get_distance_metres(vehicle.location.global_frame, new_centroid)

            #esta bloqueado si se repite ............?
            if(distance_to_new_centroid<MINIMUN_DISTANCE):
                print "RESULT MANAGER: ..................ARRIVED at centroid..........................."+s
                logging.info ("RESULT MANAGER: arrived........"+s) 
                #...para desbloquear el vuelo................
                flight_blocked+=1
                if(flight_blocked>10):
                    print "RESULT MANAGER: ...................flight blocked at centroid.................."+s
                    logging.info ("RESULT MANAGER:  ............flight blocked at centroid.........."+s)
                    #vehicle.simple_goto(W2_LOCATION)
                    previous_position=mavlink.log_vehicle_status(vehicle, "....flight blocked...", previous_position, start_time, flight_distance) 
                    break 
            elif(distance_to_new_centroid>SECURITY_DISTANCE):
                print "RESULT MANAGER: ........................centroid far away.............."+s
                logging.info ("RESULT MANAGER: centroid far away, stop flight and return........"+s)      
                #parar?
                previous_position=mavlink.log_vehicle_status(vehicle, "....new centroid far away RTL.....", previous_position, start_time, flight_distance)               
                #sigue el bucle para tener telemetria
                #continue_processing=False 
                flight_blocked=0 
                break
            else:
                flight_blocked=0                
                #################################################################
                #wait until arrives.....??? if finished before ???....use WSR                
                print "RESULT MANAGER: ...............DSF GOTO new centroid ............................. "

                vehicle.mode = VehicleMode("GUIDED")

                while not vehicle.mode.name=='GUIDED':  #Wait until mode has changed
                    print " Waiting for GUIDED mode  ..."
                    time.sleep(1)

                vehicle.simple_goto(new_centroid)
                while distance_to_new_centroid>MINIMUN_DISTANCE:
                    
                    try:
                        mqp.send(str(previous_position.lat)+","+str(previous_position.lon),1)
                    except posix_ipc.BusyError: 
                        print("....................timeout sending position........")

                    previous_position= mavlink.log_vehicle_status(vehicle, "...TELEMETRY....", previous_position, start_time, flight_distance) 
                    time.sleep(1)
                    distance_to_new_centroid=util.get_distance_metres(vehicle.location.global_frame, new_centroid)
                
                print "RESULT MANAGER: ...............DSF GOTO new centroid FINISHED............................. "
                vehicle.mode = VehicleMode("AUTO")
                while not vehicle.mode.name=='AUTO':  #Wait until mode has changed
                    print " Waiting for AUTO mode  ..."
                    time.sleep(1)

              
              
    loop += 1
    print("RESULT MANAGER: ..................loop "+str(loop)+" completed  "+s)    
    logging.debug("RESULT MANAGER: loop "+str(loop)+" completed  "+s)  
    
    time.sleep(1)

###############################################
print 'RESULT MANAGER:...............Return to launch................'
logging.debug ("RESULT MANAGER: RTL........")                   
previous_position=mavlink.log_vehicle_status(vehicle, "....RTL....."+s, previous_position, start_time, flight_distance)  

mavlink.set_RTL_mode(vehicle)

while True:
    stop_distance = mavlink.distance_UAS_to_home(vehicle)
    print " Altitude: ", vehicle.location.global_relative_frame.alt 
    #Break and return from function just below target altitude. 
    print " distance to home : ", stop_distance 
    
    if (vehicle.location.global_relative_frame.alt<0.2 and stop_distance<MINIMUN_DISTANCE): 
        print "Reached home position & altitude............."
        break

    time.sleep(1)  
    previous_position=mavlink.log_vehicle_status(vehicle, "....RTL...."+s, previous_position, start_time, flight_distance)    


print "\nSet Vehicle.mode = LAND (currently: %s)" % vehicle.mode.name 
vehicle.mode = VehicleMode("LAND")
while not vehicle.mode.name=='LAND':  #Wait until mode has changed
    print " Waiting for LAND mode  ..."
    time.sleep(1)


print "\nSet Vehicle.armed=False (currently: %s)" % vehicle.armed
vehicle.armed = False

while vehicle.armed:      
    print " Waiting for disarming..."
    print " Vehicle.armed currently: %s " % vehicle.armed
    time.sleep(1)


#Close vehicle object before exiting script
print "Close vehicle object"
vehicle.close()

print("RESULT MANAGER: ..........................FLIGHT END ...................................... ")    
logging.debug("RESULT MANAGER: ENDED  ")  
sys.exit(0)