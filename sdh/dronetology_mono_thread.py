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
import datetime
import shutil
import random
import os

logging.basicConfig(format='%(asctime)s %(message)s', filename='./log/dronetology.log',level=logging.DEBUG)


# 3rd party modules
import posix_ipc

# Import DroneKit-Python
from dronekit import connect, VehicleMode, LocationGlobalRelative

import imp

mavlink = imp.load_source('mavlink', './mavlink/mavlink.py')
inference = imp.load_source('inference', './inference/inference.py')
sensor = imp.load_source('sensor', './util/sensor.py')
util = imp.load_source('util', './util/util.py')

MAX_SECURITY_LOOP=380
SECURITY_DISTANCE=400
MINIMUN_DISTANCE=10


#####################################################################
def etl(flight_params, sensor_id):

    util.addHarvestedSensor(flight_params, sensor_id)   


def repeated_connection():
    
    SERIAL_CONNECTION_STRING="/dev/ttyUSB0"

    print 'DATA SOURCE MANAGER:Serial port init................'
    logging.debug( 'DATA SOURCE MANAGER:Serial port init...........')

    try_connection=5

    while try_connection>1:
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
            try_connection=0

        except exceptions as other_error:
            #print 'DATA SOURCE MANAGER:Serial port error.....exit'
            #logging.error( 'DATA SOURCE MANAGER:Serial port error....exit')
            try_connection=try_connection-1
            ser=None
            time.sleep(0.5)
            logging.error( 'DATA SOURCE MANAGER: try connection again.........')
            print ('DATA SOURCE MANAGER: try connection again.........')
    
    return ser

#####################################################################
def receive_sensors_debug(flight_params, vehicle, harvested_sensors):

    sensors_locations=sensor.sensors_locations(flight_params)

    if len(harvested_sensors)<4:
        for s_position in sensors_locations:
            sensor_distance=util.get_distance_metres_3d(s_position, vehicle.location.global_relative_frame)
            if( (sensor_distance-random.randint(1, 15))<30):                    
                sensor_id=sensors_locations.index(s_position)+1
                if(sensor_id in harvested_sensors):                        
                    print("DATA SOURCE MANAGER: Sensor already harvested "+str(sensor_id))
                else:
                    harvested_sensors.append(sensor_id)                       
                    etl(flight_params,sensor_id)
                    print("DATA SOURCE MANAGER: ................harvested sensor "+str(sensor_id)+"......pending sensors :"+str(4-len(harvested_sensors)))



#####################################################################
def receive_sensors(flight_params, vehicle, harvested_sensors):

    if (flight_params.find("debug")>-1):        
        return receive_sensors_debug(flight_params, vehicle, harvested_sensors)

    serial_connection = repeated_connection()

    if serial_connection is None:
        print ""
    else:
        x=serial_connection.readline()

        a=x.find("SENSOR ID:")
        b=x.find("END")

        aa=x.find("RSSI:")
        bb=x.find("END-RSSI")

        sensor= x[a:b].strip()
        rssi_received= x[aa:bb].strip()

        serial_connection.close()

        if(a>-1 and b>-1 and sensor):
            logging.debug("DATA SOURCE MANAGER: RSSI:"+rssi_received)
            print("DATA SOURCE MANAGER: RSSI:"+rssi_received)

            if(sensor in harvested_sensors):                        
                print("DATA SOURCE MANAGER: Sensor already harvested "+str(sensor))
            else:
                harvested_sensors.append(sensor)                       
                etl(flight_params,sensor)
                print("DATA SOURCE MANAGER: ................harvested sensor "+str(sensor)+"......pending sensors :"+str(4-len(harvested_sensors)))





#####################################################################
def run_inference(flight_params, vehicle):   

    rdf_file_name="undefined-data.rdf"

    if (flight_params.find("psa")>-1):

        if(flight_params.find("|1")>-1):    
            rdf_file_name="psa-wsn1-data.rdf"    
        if(flight_params.find("|2")>-1):    
            rdf_file_name="psa-wsn2-data.rdf"

        result=inference.sparql_wrapper(rdf_file_name, "psa.spql")

        if(result.find("xsd:int")>0):
            return "DELETE_WAYPOINT"
        else:
            return "PSAInferenceOk"

    if (flight_params.find("dsf")>-1):

        if(flight_params.find("|1")>-1):    
            rdf_file_name="dsf-wsn1-data.rdf"    
        if(flight_params.find("|2")>-1):    
            rdf_file_name="dsf-wsn2-data.rdf"  

        result=inference.sparql_wrapper(rdf_file_name, "dsf.spql")

        if(result.find('| 0   | 0   | "0')>0):
            return "END_DSF"
        else:
            b=result.find("===========================================")
            bb=result.find("|", b)
            c=result.find("---------------", b)
            
            pattern = r'"([0-9_\./\\-]*)"'        
            m = re.findall(pattern, result[bb:c])

            centroid_lat=float(m[0])/float(m[2])
            centroid_lon=float(m[1])/float(m[2])

            return "NEW_CENTROID||"+str(centroid_lat)+"|"+str(centroid_lon)


    if (flight_params.find("isa1")>-1):

        if(flight_params.find("|1")>-1):    
            rdf_file_name="isa1-wsn1-data.rdf"    
        if(flight_params.find("|2")>-1):    
            rdf_file_name="isa1-wsn2-data.rdf"      

        sparql_file_name="isa1-w1.spql"
        if(vehicle.commands.next==1 or vehicle.commands.next==2):
            sparql_file_name="isa1-w1.spql"
        elif(vehicle.commands.next==3):
            sparql_file_name="isa1-w2.spql"
        else:
            return "END_ISA1"

        result=inference.sparql_wrapper(rdf_file_name, sparql_file_name)
 
        if(result.find("avoid")>0):
            return "AVOID_NEXT_WAYPOINT||"+str(vehicle.commands.next)
        else:
            return "CONTINUE||"+str(vehicle.commands.next)

    return "noInferenceResult"



##########################################################################################################
###################################################.....................init process

flight_distance=[0]
start_time=time.time()

signal.signal(signal.SIGINT, util.signal_handler)

print("dronetology-kit monothread SDH ....starting....................."+str(datetime.datetime.now()))
logging.debug("dronetology-kit monothread SDH ....starting....................."+str(datetime.datetime.now()))

if(sys.argv[1] and sys.argv[2]):
    logging.debug('......running flight type: %s', sys.argv[1]) 
    flight_mode = str(sys.argv[1])   
    flight_type = str(sys.argv[2])
    flight_plan = str(sys.argv[3])
    flight_params=flight_mode+"|"+flight_type+"|"+flight_plan
else:
    logging.debug('......running default flight type: bfa')
    flight_params="debug|bfa|1"


logging.debug("RESULT MANAGER: flight type................."+flight_params)
print("RESULT MANAGER: flight type.............."+flight_params) 

if(flight_type=="isa1"):
    shutil.copy2('./rdf/init/isa1-wsn1-data.rdf', './rdf/isa1-wsn1-data.rdf')
    shutil.copy2('./rdf/init/isa1-wsn2-data.rdf', './rdf/isa1-wsn2-data.rdf')


if(flight_type=="dsf"):
    shutil.copy2('./rdf/init/dsf-wsn1-data.rdf', './rdf/dsf-wsn1-data.rdf')
    shutil.copy2('./rdf/init/dsf-wsn2-data.rdf', './rdf/dsf-wsn2-data.rdf')


if(flight_type=="psa"):
    shutil.copy2('./rdf/init/psa-wsn1-data.rdf', './rdf/psa-wsn1-data.rdf')
    shutil.copy2('./rdf/init/psa-wsn2-data.rdf', './rdf/psa-wsn2-data.rdf')

##.....................................


harvested_sensors=[]
sensors_visited=[]

######################################################.................vehicle conection..................

vehicle=mavlink.repeated_connection(flight_params)

print "RESULT MANAGER: connected to vehicle"
logging.debug ("RESULT MANAGER : connected to vehicle")

mavlink.init_flight(flight_params, vehicle)

loop=1

#dsf centroide que bloquea
flight_blocked=0

nextwaypoint_sent="undefined"

############## has altitude....................as relative for telemetry
previous_position=mavlink.get_home_position(vehicle)
previous_position.alt=0

inferenced="undefined"

while 1:

    previous_position= mavlink.log_vehicle_status(vehicle, "...TELEMETRY....", previous_position, start_time, flight_distance)

    nextwaypoint=vehicle.commands.next
    logging.debug("RESULT MANAGER:  flying to..........."+str(nextwaypoint))
    print("RESULT MANAGER:  flying to............. "+str(nextwaypoint))
        
    receive_sensors(flight_params, vehicle, harvested_sensors)

    inference_result=run_inference(flight_params, vehicle)
   
    if(inference_result==inferenced):        
        s="noInferenceResult"
    else:
        inferenced=inference_result
        s=inference_result
        print "............inference_resut......"+s

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

            if( (nextwaypoint>=3) and (stop_distance<MINIMUN_DISTANCE) ):
                logging.debug("RESULT MANAGER: ISA1 finish......")
                print("RESULT MANAGER: .........................ISA1 finish.......... ")    
                break

        elif (flight_params.find("dsf")>-1 and s=="noInferenceResult"):

            pending_sensor_position = inference.pending_sensor_latlon(flight_params, sensors_visited)  
            
            if( vehicle.mode.name=='AUTO' and pending_sensor_position!= None):   

                print "RESULT MANAGER: .................DSF GOTO sensors.............................. "

                distance_to_pending_sensor=util.get_distance_metres(vehicle.location.global_frame, pending_sensor_position)

                vehicle.mode = VehicleMode("GUIDED")
                while not vehicle.mode.name=='GUIDED':  #Wait until mode has changed
                    print " Waiting for GUIDED mode  ..."
                    time.sleep(1)

                vehicle.simple_goto(pending_sensor_position)
                while distance_to_pending_sensor>MINIMUN_DISTANCE:
                    time.sleep(0.5)
                    receive_sensors(flight_params, vehicle, harvested_sensors)
                    previous_position= mavlink.log_vehicle_status(vehicle, "...TELEMETRY....", previous_position, start_time, flight_distance)                     
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
                    receive_sensors(flight_params, vehicle, harvested_sensors)
                    previous_position= mavlink.log_vehicle_status(vehicle, "...TELEMETRY....", previous_position, start_time, flight_distance) 
                    time.sleep(0.5)
                    distance_to_new_centroid=util.get_distance_metres(vehicle.location.global_frame, new_centroid)
                
                print "RESULT MANAGER: ...............DSF GOTO new centroid FINISHED............................. "
                vehicle.mode = VehicleMode("AUTO")
                while not vehicle.mode.name=='AUTO':  #Wait until mode has changed
                    print " Waiting for AUTO mode  ..."
                    time.sleep(1)

              
              
    loop += 1
    print("RESULT MANAGER: ..................loop "+str(loop)+" completed  "+s)    
    logging.debug("RESULT MANAGER: loop "+str(loop)+" completed  "+s)  
    
    time.sleep(0.1)

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