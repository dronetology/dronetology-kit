#!/usr/bin/env python
import time
import logging
import exceptions
import dronekit
import csv



# Import DroneKit-Python
from dronekit import connect, VehicleMode, LocationGlobalRelative

CONNECTION_STRING="/dev/ttyS0"


def single_connection():
    try:
        #http://python.dronekit.io/guide/connecting_vehicle.html
        #115200
        #vehicle = connect("/dev/ttyACM0", wait_ready=True)
        vehicle = connect(CONNECTION_STRING, wait_ready=True, baud=57600)
        vehicle.wait_ready(True)
        log_vehicle_status(vehicle, "....Vehicle connected...")        
    except:
        logging.error( 'MAVLINK:  single_connection connection error.........')
        print ('MAVLINK: single_connection connection error.........')
        return None
    
    return vehicle

def repeated_connection():

    try_connection=True

    while try_connection:
        try:
            #http://python.dronekit.io/guide/connecting_vehicle.html
            #115200
            #vehicle = connect("/dev/ttyACM0", wait_ready=True)
            vehicle = connect(CONNECTION_STRING, wait_ready=True, baud=57600)
            vehicle.wait_ready(True)
            log_vehicle_status(vehicle, "....Vehicle connected...")
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
        except:
            print 'MAVLINK: stopped, NO CONNECTION TO VEHICLE  Some other error!'
            logging.error( 'MAVLINK: stopped, NO CONNECTION TO VEHICLE  Some other error!............')
            time.sleep(5)
            logging.error( 'MAVLINK: try connection again.........')
            print ('MAVLINK: try connection again.........')

    return vehicle


def set_home_position(vehicle, aTargetAltitude):
    print "\nSet new home location"
    # Home location must be within 50km of EKF home location (or setting will fail silently)
    # In this case, just set value to current location with an easily recognisable altitude (222)
    my_location_alt = vehicle.location.global_frame
    my_location_alt.alt = aTargetAltitude
    vehicle.home_location = my_location_alt
    print " New Home Location (from attribute - altitude should be "+aTargetAltitude+"): %s" % vehicle.home_location

    #Confirm current value on vehicle by re-downloading commands
    cmds = vehicle.commands
    cmds.download()
    cmds.wait_ready()
    print " Confirm ....New Home Location (from vehicle - altitude should be "+aTargetAltitude+"): %s" % vehicle.home_location

    return


def set_RTL_mode(vehicle):
    vehicle.mode = VehicleMode("RTL")
    while not vehicle.mode.name=='RTL':  #Wait until mode has changed
        print "MAVLINK: Waiting for mode change ..."
        logging.debug("MAVLINK: Waiting for mode change ...")
        time.sleep(1)


def get_home_location(vehicle):

    while not vehicle.home_location:
        cmds = vehicle.commands
        cmds.download()
        cmds.wait_ready()
        if not vehicle.home_location:
            print " Waiting for home location ..."
            logging.debug(" Waiting for home location ...")


    # We have a home location, so print it!        
    logging.debug("TELEMETRY: Home location: %s" % vehicle.home_location)

    return

def log_vehicle_status(vehicle=None, timeMessage=""):
    vehicle=single_connection()
    return log_vehicle_status(vehicle, timeMessage)

## from http://python.dronekit.io/examples/simple_goto.html
def arm_and_takeoff(vehicle, aTargetAltitude):
    """
    Arms vehicle and fly to aTargetAltitude.
    """

    print "Basic pre-arm checks"
    # Don't try to arm until autopilot is ready
    while not vehicle.is_armable:
        print " Waiting for vehicle to initialise..."
        time.sleep(1)

        
    print "Arming motors"
    # Copter should arm in GUIDED mode
    vehicle.mode = VehicleMode("GUIDED")
    vehicle.armed = True    

    # Confirm vehicle armed before attempting to take off
    while not vehicle.armed:      
        print " Waiting for arming..."
        time.sleep(1)

    print "Taking off!"
    vehicle.simple_takeoff(aTargetAltitude) # Take off to target altitude

    # Wait until the vehicle reaches a safe height before processing the goto (otherwise the command 
    #  after Vehicle.simple_takeoff will execute immediately).
    while True:
        print " Altitude: ", vehicle.location.global_relative_frame.alt 
        #Break and return from function just below target altitude.        
        if vehicle.location.global_relative_frame.alt>=aTargetAltitude*0.95: 
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

def log_vehicle_status(vehicle, timeMessage="", timeReference=0):
 
    print("TELEMETRY:..."+timeMessage+"..GPS: %s....Battery: %s.....Last Heartbeat: %s....Is Armable?: %s...System status: %s....Mode: %s", vehicle.location.global_frame, vehicle.battery, vehicle.last_heartbeat, vehicle.is_armable, vehicle.system_status.state, vehicle.mode.name)
    
    logging.debug("TELEMETRY:..."+timeMessage+"..GPS: %s....Battery: %s.....Last Heartbeat: %s....Is Armable?: %s...System status: %s....Mode: %s", vehicle.location.global_frame, vehicle.battery, vehicle.last_heartbeat, vehicle.is_armable, vehicle.system_status.state, vehicle.mode.name)
    
    with open('telemetry.csv', 'a') as csvfile:
        writer = csv.writer(csvfile, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)        
        #writer.writerow(['time', 'lat', 'lon', 'bat'])
        if(timeReference==0):
            writer.writerow([time.time(), 0, vehicle.location.global_relative_frame.lat, vehicle.location.global_relative_frame.lon, vehicle.location.global_relative_frame.alt, vehicle.battery.level])
        else:
            write_time=time.time()
            writer.writerow([write_time, write_time-timeReference, vehicle.location.global_relative_frame.lat, vehicle.location.global_relative_frame.lon, vehicle.location.global_relative_frame.alt, vehicle.battery.level])

    return
