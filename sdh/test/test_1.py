#!/usr/bin/env python
import time
import dronekit
import math
import os


# 3rd party modules
import posix_ipc

from pymavlink import mavutil
# Import DroneKit-Python
from dronekit import connect, VehicleMode, LocationGlobalRelative, Command


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


try:     
    mqs = posix_ipc.MessageQueue("/FLIGHT_TYPE_QUEUE")  
except posix_ipc.ExistentialError:   
    mqs = posix_ipc.MessageQueue("/FLIGHT_TYPE_QUEUE")

#blocked until receive flight type..........................................
print 'test1: waiting for flight_type...............'

flight_params= mqs.receive()[0] 
#para evitar que se quede vacia
mqs.send(flight_params)   

###################################
DRONE_CONNECTION_STRING="/dev/ttyS0"
DEBUG_CONNECTION_STRING="127.0.0.1:14550"

target_altitude=20


if(flight_params.find("debug")>-1):
    connection_local=DEBUG_CONNECTION_STRING
else:
    connection_local=DRONE_CONNECTION_STRING

vehicle = connect(connection_local, wait_ready=True, baud=57600)

print "Test 1: connected to vehicle"

print ".....home altitude..relative...%s..........." % vehicle.location.global_relative_frame.alt
print ".....home altitude.....%s..........." % vehicle.location.global_frame.alt

######################################


#####################################

# Get Vehicle Home location - will be `None` until first set by autopilot
while not vehicle.home_location:
    cmds = vehicle.commands
    cmds.download()
    cmds.wait_ready()
    if not vehicle.home_location:
        print " Waiting for home location ..."
# We have a home location, so print it!        
print "\n Home location: %s" % vehicle.home_location

######################################
print " Global Location: %s" % vehicle.location.global_frame
print " Global Location (relative altitude): %s" % vehicle.location.global_relative_frame

#################3comprueba home , y gps near

distance_to_home=get_distance_metres(vehicle.location.global_relative_frame, vehicle.home_location)

while distance_to_home>10:
    print "...........home and gps too far away........"+str(distance_to_home)
    print " GPS: %s" % vehicle.gps_0
    print "\nVehicle.mode  currently: %s" % vehicle.mode.name 
    distance_to_home=get_distance_metres(vehicle.location.global_relative_frame, vehicle.home_location)
    time.sleep(1)

#############comprueba ejecuta tmux

#https://unix.stackexchange.com/questions/10689/how-can-i-tell-if-im-in-a-tmux-session-from-a-bash-script
if(os.environ['TERM']=="screen"):
    print ".....in TMUX..........." 
else:
    print ".....NOT using TMUX..........."

#################################################3

cmds = vehicle.commands

print " Clear any existing commands"
cmds.clear() 
cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, 0, 0, 0, 0, 0, 0, 0, 0, 10))

print " Upload new commands to vehicle"
cmds.upload()
#####################################

# Copter should arm in Guided-mode
vehicle.mode = VehicleMode("STABILIZE")

#####################################
while not vehicle.is_armable:
    print " Waiting for vehicle to initialise..."
    time.sleep(1)
        
print "Arming motors"
print "\nSet Vehicle.mode = GUIDED (currently: %s)" % vehicle.mode.name 
# Copter should arm in GUIDED mode
vehicle.mode = VehicleMode("GUIDED")
vehicle.armed = True  
vehicle.flush()

while not vehicle.armed:     
    print " Waiting for arming..."
    time.sleep(1)    

print "Taking off!"
vehicle.simple_takeoff(target_altitude) # Take off to target altitude

while True:
    print " Altitude: ", vehicle.location.global_relative_frame.alt 
    print " test1.............mode:"+vehicle.mode.name
    #Break and return from function just below target altitude.        
    if vehicle.location.global_relative_frame.alt>=target_altitude*0.95: 
        print "Reached target altitude"
        break
    time.sleep(1)


######################################

print "\nSet Vehicle.mode = LAND (currently: %s)" % vehicle.mode.name 
vehicle.mode = VehicleMode("LAND")
while not vehicle.mode.name=='LAND':  #Wait until mode has changed
    print " Waiting for mode change ..."
    time.sleep(1)

while True:
    print " Altitude: ", vehicle.location.global_relative_frame.alt 
    print " test1..............mode:"+vehicle.mode.name
    #Break and return from function just below target altitude.        
    if vehicle.location.global_relative_frame.alt<0.15: 
        print "Reached land"
        break
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

print(" END ******************************************************************* ")    

