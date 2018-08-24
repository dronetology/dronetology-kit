#!/usr/bin/env python
import time
import logging
import exceptions
import dronekit
import csv
import math
import os
import sys

import imp

flight_plan_1 = imp.load_source('flight_plan_1', './conf/flight_plan_1.py')
flight_plan_2 = imp.load_source('flight_plan_2', './conf/flight_plan_2.py')
flight_plan_3 = imp.load_source('flight_plan_3', './conf/flight_plan_3.py')

util = imp.load_source('util', './util/util.py')


from pymavlink import mavutil
# Import DroneKit-Python
from dronekit import connect, VehicleMode, LocationGlobalRelative, LocationGlobal, Command

DRONE_CONNECTION_STRING="/dev/ttyS0"
DEBUG_CONNECTION_STRING_TCP="tcp:127.0.0.1:5760"
DEBUG_CONNECTION_STRING="127.0.0.1:14550"

########### constantes ######################


VEHICLE_VELOCITY=2
#................. /home/david/.dronekit/sitl/copter-3.3/apm --home=-42.8305481,-1.730344,10,353 --model=quad   



def single_connection():
    try:
        #http://python.dronekit.io/guide/connecting_vehicle.html
        #115200
        #vehicle = connect("/dev/ttyACM0", wait_ready=True, baud=57600)
        #vehicle = connect("/dev/ttyACM0", wait_ready=True, baud=57600)
        vehicle = connect(CONNECTION_STRING, wait_ready=True, baud=57600)
        vehicle.wait_ready(True)              
    except:
        logging.error( 'MAVLINK:  single_connection connection error.........')
        print ('MAVLINK: single_connection connection error.........')
        return None
    
    return vehicle

def repeated_connection(flight_params):

    try_connection=True

    connection_local=DEBUG_CONNECTION_STRING

    if(flight_params.find("debug")>-1):
        connection_local=DEBUG_CONNECTION_STRING
    else:
        connection_local=DRONE_CONNECTION_STRING


    while try_connection:
        try:
            #http://python.dronekit.io/guide/connecting_vehicle.html
            #115200
            #vehicle = connect("/dev/ttyACM0", wait_ready=True, baud=57600)
            #vehicle = connect("/dev/ttyS0", wait_ready=True, baud=57600            
            vehicle = connect(connection_local, wait_ready=True, baud=57600)
            #vehicle.wait_ready(True)            
            try_connection=False

        # Bad TTY connection
        except exceptions.OSError as e:
            print 'MAVLINK: stopped, NO CONNECTION TO VEHICLE  No serial exists!'
            logging.error( 'MAVLINK: stopped, NO CONNECTION TO VEHICLE No serial exists!..........')
            time.sleep(5)
            logging.error( 'MAVLINK: try connection again.........')
            print ('MAVLINK: try connection again.........')

        # API Error
        except dronekit.APIException:
            print 'MAVLINK: stopped, NO CONNECTION TO VEHICLE  Timeout!'
            logging.error( 'MAVLINK: stopped, NO CONNECTION TO VEHICLE  Timeout!..........')
            time.sleep(5)
            logging.error( 'MAVLINK: try connection again.........')
            print ('MAVLINK: try connection again.........')
        # Other error
        except exceptions as other_error:
            print 'MAVLINK: stopped, NO CONNECTION TO VEHICLE  Some other error!'
            logging.error( 'MAVLINK: stopped, NO CONNECTION TO VEHICLE  Some other error!............')
            time.sleep(5)
            logging.error( 'MAVLINK: try connection again.........')
            print ('MAVLINK: try connection again.........')

    return vehicle


def set_home_position_notused(flight_params, vehicle):

    print "\nSet new home location"
    # Home location must be within 50km of EKF home location (or setting will fail silently)
    # In this case, just set value to current location with an easily recognisable altitude (222)
   
    my_location_alt = vehicle.location.global_frame

    if(flight_params.find("|1")>-1):
        my_location_alt.lat = flight_plan_1.HOME_LOCATION_LAT
        my_location_alt.lon = flight_plan_1.HOME_LOCATION_LON
        my_location_alt.alt = flight_plan_1.HOME_LOCATION_ALT
    elif(flight_params.find("|2")>-1):
        my_location_alt.lat = flight_plan_2.HOME_LOCATION_LAT
        my_location_alt.lon = flight_plan_2.HOME_LOCATION_LON
        my_location_alt.alt = flight_plan_2.HOME_LOCATION_ALT
    elif(flight_params.find("|3")>-1):
        my_location_alt.lat = flight_plan_3.HOME_LOCATION_LAT
        my_location_alt.lon = flight_plan_3.HOME_LOCATION_LON
        my_location_alt.alt = flight_plan_3.HOME_LOCATION_ALT

    vehicle.home_location = my_location_alt
    
    print " New Home Location : %s" % vehicle.home_location
    
    time.sleep(2)


    #Confirm current value on vehicle by re-downloading commands
    cmds = vehicle.commands
    cmds.download()
    cmds.wait_ready()
    print " Confirm ....New Home Location: %s" % vehicle.home_location
    print " Confirm ....current position...............: %s" % vehicle.location.global_frame

    return


def set_RTL_mode(vehicle):
    vehicle.mode = VehicleMode("RTL")
    while not vehicle.mode.name=='RTL':  #Wait until mode has changed
        print "MAVLINK: Waiting for RTL mode  ..."
        logging.debug("MAVLINK: Waiting for RTL mode ...")
        time.sleep(1)
    
    print vehicle.mode


def get_home_location(vehicle):

    while not vehicle.home_location:
        cmds = vehicle.commands
        cmds.download()
        cmds.wait_ready()
        if not vehicle.home_location:
            print " Waiting for home location ..."
            logging.debug(" Waiting for home location ...")


    # We have a home location, so print it!  
    print("TELEMETRY: Home location: %s" % vehicle.home_location)    
    logging.debug("TELEMETRY: Home location: %s" % vehicle.home_location)

    return vehicle.home_location

def log_vehicle_status(vehicle=None, timeMessage=""):
    vehicle=single_connection()   
    return log_vehicle_status(vehicle, timeMessage)

def get_home_position(vehicle):
    return vehicle.home_location

def generate_point(flight_params, m):
    if(flight_params.find("|1")>-1):
        return LocationGlobalRelative(float(m[0]), float(m[1]), flight_plan_1.TARGET_ALTITUDE)
    elif(flight_params.find("|2")>-1):
        return LocationGlobalRelative(float(m[0]), float(m[1]), flight_plan_2.TARGET_ALTITUDE)
    elif(flight_params.find("|3")>-1):
        return LocationGlobalRelative(float(m[0]), float(m[1]), flight_plan_3.TARGET_ALTITUDE)

    

def distance_UAS_to_home(vehicle):
    return util.get_distance_metres(vehicle.location.global_relative_frame, vehicle.home_location)

def distance_to_home(vehicle, point):
    return util.get_distance_metres(vehicle.home_location, point)


def read_channels(vehicle):
    # Access channels individually
    print "Read channels individually:"
    print " Ch1: %s" % vehicle.channels['1']
    print " Ch2: %s" % vehicle.channels['2']
    print " Ch3: %s" % vehicle.channels['3']
    print " Ch4: %s" % vehicle.channels['4']
    print " Ch5: %s" % vehicle.channels['5']
    print " Ch6: %s" % vehicle.channels['6']
    print " Ch7: %s" % vehicle.channels['7']
    print " Ch8: %s" % vehicle.channels['8']
    print "Number of channels: %s" % len(vehicle.channels)


def clear_mission(vehicle):

    cmds = vehicle.commands

    print " Clear any existing commands"
    cmds.clear() 

    return cmds


def init_flight(flight_params, vehicle):  


    #############comprueba ejecuta tmux
    #https://unix.stackexchange.com/questions/10689/how-can-i-tell-if-im-in-a-tmux-session-from-a-bash-script
    
    if(os.environ['TERM']=="screen"):
        print ".....in TMUX..........." 
    else:
        print " not tmux"
        #sys.exit(0)

    # Get Vehicle Home location - will be `None` until first set by autopilot
    while not vehicle.home_location:
        cmds = vehicle.commands
        cmds.download()
        cmds.wait_ready()
        if not vehicle.home_location:
            print " Waiting for home location ..."

    # We have a home location, so print it!        
    print "\n Home location: %s" % vehicle.home_location

    #############################
    distance_to_home=util.get_distance_metres(vehicle.location.global_relative_frame, vehicle.home_location)

    while distance_to_home>10:
        print "...........home and gps too far away........"+str(distance_to_home)
        print " GPS: %s" % vehicle.gps_0
        print "\nVehicle.mode  currently: %s" % vehicle.mode.name 
        distance_to_home=util.get_distance_metres(vehicle.location.global_relative_frame, vehicle.home_location)
        time.sleep(1)


    print " Confirm ....New Home Location: %s" % vehicle.home_location
    print " Confirm ....current position...............: %s" % vehicle.location.global_frame
    
    
    print 'Create a new mission (for current location)'
    adds_mission(flight_params, vehicle, vehicle.home_location)   
    #vehicle.mode = VehicleMode("LOITER")

    print vehicle.mode

    arm_and_takeoff(flight_params, vehicle)

    print "Starting mission"
    # Reset mission set to first (0) waypoint
    vehicle.commands.next=0

    # Set mode to AUTO to start mission
    vehicle.mode = VehicleMode("AUTO")

    while not vehicle.mode.name=='AUTO':  #Wait until mode has changed
        print " Waiting for AUTO mode  ..."
        time.sleep(1)

    print vehicle.mode

    

## from http://python.dronekit.io/examples/simple_goto.html
def arm_and_takeoff(flight_params, vehicle):
    """
    Arms vehicle and fly to aTargetAltitude.
    """
    # Copter should arm in Guided-mode    

    print "Basic pre-arm checks"
    # Don't try to arm until autopilot is ready
    while not vehicle.is_armable:
        print " Waiting for vehicle to initialise..."
        time.sleep(1)

        
    print "Arming motors"
    # Copter should arm in GUIDED mode
    vehicle.mode = VehicleMode("GUIDED")
    vehicle.flush() 
    vehicle.armed = True   
    vehicle.flush() 

    #..............armed check and control....................
    #.....>>> PreArm: RC not calibrated......https://github.com/ArduPilot/MAVProxy/issues/11
    #vehicle.parameters['ARMING_CHECK']=0
    loops_max=0

    # Confirm vehicle armed before attempting to take off
    while not vehicle.armed:     
        print " Waiting for arming..."
        time.sleep(1)
        loops_max+=1        

    print "Taking off!"

    if(flight_params.find("|1")>-1):
        target_altitude=flight_plan_1.TARGET_ALTITUDE
    elif(flight_params.find("|2")>-1):
        target_altitude=flight_plan_2.TARGET_ALTITUDE
    elif(flight_params.find("|3")>-1):
        target_altitude=flight_plan_3.TARGET_ALTITUDE

    vehicle.simple_takeoff(target_altitude) # Take off to target altitude

    # Wait until the vehicle reaches a safe height before processing the goto (otherwise the command 
    #  after Vehicle.simple_takeoff will execute immediately).
    while True:
        print " Altitude: ", vehicle.location.global_relative_frame.alt 
        #Break and return from function just below target altitude.        
        if vehicle.location.global_relative_frame.alt>=target_altitude*0.95: 
            print "Reached target altitude"
            break
        time.sleep(1)


def print_vehicle_status(vehicle, timeMessage=""):
 
    logging.basicConfig(format='%(asctime)s %(message)s', filename='telemetry.log',level=logging.DEBUG)

    # Get some vehicle attributes (state)
    print "Get some vehicle attribute values:"
    print " GPS: %s" % vehicle.gps_0
    print " Battery: %s" % vehicle.battery
    print " Last Heartbeat: %s" % vehicle.last_heartbeat
    print " Is Armable?: %s" % vehicle.is_armable
    print " System status: %s" % vehicle.system_status.state
    print " Mode: %s" % vehicle.mode.name    # settable

    print(vehicle.location.global_frame)

    logging.debug("TELEMETRY:..."+timeMessage+"..GPS: %s....Battery: %s.....Last Heartbeat: %s.....Is Armable?: %s...System status: %s....Mode: %s", vehicle.gps_0, vehicle.battery, vehicle.last_heartbeat, vehicle.is_armable, vehicle.system_status.state, vehicle.mode.name)
    return


def log_vehicle_status(vehicle, timeMessage, previous_position, time_reference, distance_accumulated):
 
    #print("TELEMETRY:..."+timeMessage+"..GPS: %s....Battery: %s.....Last Heartbeat: %s....Is Armable?: %s...System status: %s....Mode: %s", vehicle.location.global_frame, vehicle.battery, vehicle.last_heartbeat, vehicle.is_armable, vehicle.system_status.state, vehicle.mode.name)
    
    logging.debug("TELEMETRY:..."+timeMessage+"..GPS: %s..Attitude: %s...Battery: %s.....Last Heartbeat: %s....Is Armable?: %s...System status: %s....Mode: %s", vehicle.location.global_frame, vehicle.attitude, vehicle.battery, vehicle.last_heartbeat, vehicle.is_armable, vehicle.system_status.state, vehicle.mode.name)
    
    with open('./log/telemetry.csv', 'a') as csvfile:
        writer = csv.writer(csvfile, delimiter=';', quotechar='|', quoting=csv.QUOTE_MINIMAL)        
        #writer.writerow(['time', 'lat', 'lon', 'bat'])
        if(time_reference==0):
            writer.writerow([time.time(), 0, 0, vehicle.location.global_relative_frame.lat, vehicle.location.global_relative_frame.lon, vehicle.location.global_relative_frame.alt, vehicle.battery.level])
        else:
            write_time=time.time()            
            step_distance=util.get_distance_metres_3d(previous_position, vehicle.location.global_relative_frame)
            distance_accumulated.append(distance_accumulated[0]+step_distance)
            distance_accumulated.pop(0)
            writer.writerow([write_time, write_time-time_reference, distance_accumulated[0], step_distance, vehicle.location.global_relative_frame.lat, vehicle.location.global_relative_frame.lon, vehicle.location.global_relative_frame.alt, vehicle.battery.level])

    return vehicle.location.global_relative_frame


def adds_mission(flight_params, vehicle, HOME_LOCATION):
    """
    Adds a takeoff command and four waypoint commands to the current mission. 
    The waypoints are positioned to form a square of side length 2*aSize around the specified LocationGlobal (aLocation).

    The function assumes vehicle.commands matches the vehicle mission state 
    (you must have called download at least once in the session and after clearing the mission)
    """	

    #no se puede dejar la mision anterior en el drone 
    print " Clearing mission stored......."   
    cmds=clear_mission(vehicle)

    print " Define/add new commands."
    # Add new commands. The meaning/order of the parameters is documented in the Command class. 
     
    #Add MAV_CMD_NAV_TAKEOFF command. This is ignored if the vehicle is already in the air.
    cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, 0, 0, 0, 0, 0, 0, 0, 0, 10))
    
    if(flight_params.find("|1")>-1):
        if((flight_params.find("bfa")>-1)  or (flight_params.find("isa1")>-1)):
            cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, flight_plan_1.W1_LOCATION.lat, flight_plan_1.W1_LOCATION.lon, 11))
            cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, flight_plan_1.W2_LOCATION.lat, flight_plan_1.W2_LOCATION.lon, 12))
            cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, HOME_LOCATION.lat, HOME_LOCATION.lon, 13))
        elif(flight_params.find("psa")>-1):
            cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, flight_plan_1.W1_LOCATION.lat, flight_plan_1.W1_LOCATION.lon, 11))
            cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, HOME_LOCATION.lat, HOME_LOCATION.lon, 12))
        elif(flight_params.find("isa1..........not used........")>-1):
            cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, flight_plan_1.W1_PREV_LOCATION.lat, flight_plan_1.W1_PREV_LOCATION.lon, 11))
            cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, HOME_LOCATION.lat, HOME_LOCATION.lon, 12))
        elif(flight_params.find("dsf")>-1):
            cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, flight_plan_1.W1_CENTROID_LOCATION.lat, flight_plan_1.W1_CENTROID_LOCATION.lon, 11))
            cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, HOME_LOCATION.lat, HOME_LOCATION.lon, 12))
         
    elif (flight_params.find("|2")>-1):
        if( (flight_params.find("bfa")>-1) or (flight_params.find("isa1")>-1)  ):
            cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, flight_plan_2.W1_LOCATION.lat, flight_plan_2.W1_LOCATION.lon, 11))
            cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, flight_plan_2.W2_LOCATION.lat, flight_plan_2.W2_LOCATION.lon, 12))
            cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, HOME_LOCATION.lat, HOME_LOCATION.lon, 13))
        elif(flight_params.find("psa")>-1):
            cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, flight_plan_2.W1_LOCATION.lat, flight_plan_2.W1_LOCATION.lon, 11))
            cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, flight_plan_2.W2_LOCATION.lat, flight_plan_2.W2_LOCATION.lon, 12))
            cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, HOME_LOCATION.lat, HOME_LOCATION.lon, 13))
        elif(flight_params.find("isa1.....not used.......")>-1):
            cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, flight_plan_2.W1_PREV_LOCATION.lat, flight_plan_2.W1_PREV_LOCATION.lon, 11))
            cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, flight_plan_2.W2_PREV_LOCATION.lat, flight_plan_2.W2_PREV_LOCATION.lon, 12))
            cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, HOME_LOCATION.lat, HOME_LOCATION.lon, 13))
        elif(flight_params.find("dsf")>-1):
            cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, flight_plan_2.W1_CENTROID_LOCATION.lat, flight_plan_2.W1_CENTROID_LOCATION.lon, 11))
            cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, HOME_LOCATION.lat, HOME_LOCATION.lon, 12))
         
    elif (flight_params.find("|3")>-1):
        if(flight_params.find("bfa")>-1):
            cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, flight_plan_3.W1_LOCATION.lat, flight_plan_3.W1_LOCATION.lon, 11))
            cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, flight_plan_3.W2_LOCATION.lat, flight_plan_3.W2_LOCATION.lon, 12))
            cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, HOME_LOCATION.lat, HOME_LOCATION.lon, 13))
        elif(flight_params.find("psa")>-1):
            cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, flight_plan_3.W1_LOCATION.lat, flight_plan_3.W1_LOCATION.lon, 11))
            cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, flight_plan_3.W2_LOCATION.lat, flight_plan_3.W2_LOCATION.lon, 12))
            cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, HOME_LOCATION.lat, HOME_LOCATION.lon, 13))
        elif(flight_params.find("isa1")>-1):
            cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, flight_plan_3.W1_PREV_LOCATION.lat, flight_plan_3.W1_PREV_LOCATION.lon, 11))
            cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, flight_plan_3.W2_PREV_LOCATION.lat, flight_plan_3.W2_PREV_LOCATION.lon, 12))
            cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, HOME_LOCATION.lat, HOME_LOCATION.lon, 13))
        elif(flight_params.find("dsf")>-1):
            cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, flight_plan_3.W1_C1_LOCATION.lat, flight_plan_3.W1_C1_LOCATION.lon, 11))
            cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, flight_plan_3.W2_CT_LOCATION.lat, flight_plan_3.W2_CT_LOCATION.lon, 12))
            cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, flight_plan_3.W3_C2_LOCATION.lat, flight_plan_3.W3_C2_LOCATION.lon, 13))
            cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, HOME_LOCATION.lat, HOME_LOCATION.lon, 14))

    print " Upload new commands to vehicle"
    cmds.upload()



