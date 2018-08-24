#!/usr/bin/env python
import time
import math

import dronekit

# 3rd party modules
import posix_ipc

from pymavlink import mavutil
# Import DroneKit-Python
from dronekit import connect, VehicleMode, LocationGlobalRelative, LocationGlobal, Command



def get_location_metres(original_location, dNorth, dEast):
    """
    Returns a LocationGlobal object containing the latitude/longitude `dNorth` and `dEast` metres from the 
    specified `original_location`. The returned Location has the same `alt` value
    as `original_location`.

    The function is useful when you want to move the vehicle around specifying locations relative to 
    the current vehicle position.
    The algorithm is relatively accurate over small distances (10m within 1km) except close to the poles.
    For more information see:
    http://gis.stackexchange.com/questions/2951/algorithm-for-offsetting-a-latitude-longitude-by-some-amount-of-meters
    """
    earth_radius=6378137.0 #Radius of "spherical" earth
    #Coordinate offsets in radians
    dLat = dNorth/earth_radius
    dLon = dEast/(earth_radius*math.cos(math.pi*original_location.lat/180))

    #New position in decimal degrees
    newlat = original_location.lat + (dLat * 180/math.pi)
    newlon = original_location.lon + (dLon * 180/math.pi)

    return LocationGlobal(newlat, newlon,original_location.alt)


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


def distance_to_current_waypoint(vehicle):
    """
    Gets distance in metres to the current waypoint. 
    It returns None for the first waypoint (Home location).
    """
    nextwaypoint = vehicle.commands.next
    if nextwaypoint==0:
        return None

    missionitem=vehicle.commands[nextwaypoint-1] #commands are zero indexed
    lat = missionitem.x
    lon = missionitem.y
    alt = missionitem.z
    targetWaypointLocation = LocationGlobalRelative(lat,lon,alt)
    distancetopoint = get_distance_metres(vehicle.location.global_frame, targetWaypointLocation)

    return distancetopoint    


try:     
    mqs = posix_ipc.MessageQueue("/FLIGHT_TYPE_QUEUE")  
except posix_ipc.ExistentialError:   
    mqs = posix_ipc.MessageQueue("/FLIGHT_TYPE_QUEUE")

#blocked until receive flight type..........................................
print 'test2: waiting for flight_type...............'

flight_params= mqs.receive()[0] 
#para evitar que se quede vacia
mqs.send(flight_params)    

#####################################

DRONE_CONNECTION_STRING="/dev/ttyS0"
DEBUG_CONNECTION_STRING_NOPROXY="tcp:127.0.0.1:5760"
DEBUG_CONNECTION_STRING="127.0.0.1:14550"

target_altitude=10

if(flight_params.find("debug")>-1):
    connection_local=DEBUG_CONNECTION_STRING
else:
    connection_local=DRONE_CONNECTION_STRING

vehicle = connect(connection_local, wait_ready=True, baud=57600)

print "Test 1: connected to vehicle"

print " Global Location: %s" % vehicle.location.global_frame

print ".....home altitude..relative...%s..........." % vehicle.location.global_relative_frame.alt
print ".....home altitude.....%s..........." % vehicle.location.global_frame.alt

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

home_location=vehicle.location.global_relative_frame
print " Global Location: %s" % vehicle.location.global_frame
print " Global Location (relative altitude): %s" % vehicle.location.global_relative_frame


point1 = get_location_metres(vehicle.home_location, 0, -10)

######################################

cmds = vehicle.commands

print " Clear any existing commands"
cmds.clear() 
cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, 0, 0, 0, 0, 0, 0, 0, 0, 10))
cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, point1.lat, point1.lon, 11))

print " Upload new commands to vehicle"
cmds.upload()

#####################################

while not vehicle.is_armable:
    print " Waiting for vehicle to initialise..."
    time.sleep(1)
        
print "Arming motors"
print "\nSet Vehicle.mode = GUIDED (currently: %s)" % vehicle.mode.name 
# Copter should arm in GUIDED mode
vehicle.mode = VehicleMode("GUIDED")
vehicle.armed = True  

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


distance_to_waypoint=get_distance_metres(vehicle.location.global_relative_frame, point1)

######################################

print "Starting mission"
# Reset mission set to first (0) waypoint
vehicle.commands.next=0

# Set mode to AUTO to start mission
vehicle.mode = VehicleMode("AUTO")

print vehicle.mode


##########################################

while distance_to_waypoint>10: 

    nextwaypoint=vehicle.commands.next      
    print " test2...........next is "+str(nextwaypoint)+"..........mode:"+vehicle.mode.name
    print " Velocity: %s" % vehicle.velocity
    distance_to_waypoint=get_distance_metres(vehicle.location.global_relative_frame, point1)
    print "test2....distance_to_waypoint....." +str(distance_to_waypoint)   
    time.sleep(1)
    

nextwaypoint=vehicle.commands.next

print "test2 .....ARRIVED........."+str(nextwaypoint)

#############################################

print 'test2: RTL..............'
vehicle.mode = VehicleMode("RTL")
while not vehicle.mode.name=='RTL':  #Wait until mode has changed
    print "test2: Waiting for RTL mode ..."    
    time.sleep(1)

print vehicle.mode

while True:    
    print " Altitude: ", vehicle.location.global_relative_frame.alt   
    print("....distance to home............"+str(get_distance_metres(vehicle.location.global_relative_frame, home_location)) ) 
    print " Velocity: %s" % vehicle.velocity
    time.sleep(1)
    if (vehicle.location.global_relative_frame.alt<0.1): 
        print "Reached land.........."
        break

##############################################


print "\nSet Vehicle.mode = LAND (currently: %s)" % vehicle.mode.name 
vehicle.mode = VehicleMode("LAND")
while not vehicle.mode.name=='LAND':  #Wait until mode has changed
    print " Waiting for LAND mode ..."
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