#!/usr/bin/env python
import time
import logging
import exceptions
import dronekit
import csv
import math
import os
import sys


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

def get_distance_metres_3d(aLocation1, aLocation2):
    """
    Returns the ground distance in metres between two LocationGlobal objects.

    This method is an approximation, and will not be accurate over large distances and close to the 
    earth's poles. It comes from the ArduPilot test code: 
    https://github.com/diydrones/ardupilot/blob/master/Tools/autotest/common.py
    """
    dlat = aLocation2.lat - aLocation1.lat
    dlong = aLocation2.lon - aLocation1.lon
    dalt = 15

    distance_2d = math.sqrt((dlat*dlat) + (dlong*dlong)) * 1.113195e5

    return math.sqrt((dalt*dalt) + (distance_2d*distance_2d))

def addHarvestedSensor(flight_params, sensor_id):
   
    rdf_file_name="undefined-data.rdf"

    if(flight_params.find("|1")>-1):
        if(flight_params.find("isa1")>-1):
            rdf_file_name="isa1-wsn1-data.rdf"
        if(flight_params.find("dsf")>-1):
            rdf_file_name="dsf-wsn1-data.rdf"
    if(flight_params.find("|2")>-1):
        if(flight_params.find("isa1")>-1):
            rdf_file_name="isa1-wsn2-data.rdf"
        if(flight_params.find("dsf")>-1):
            rdf_file_name="dsf-wsn2-data.rdf"
    if(flight_params.find("|3")>-1):
        if(flight_params.find("isa1")>-1):
            rdf_file_name="isa1-wsn3-data.rdf"
        if(flight_params.find("dsf")>-1):
            rdf_file_name="dsf-wsn3-data.rdf"

    s='<isFlightOf rdf:resource="http://www.dronetology.net/dronetology-sdh.owl#sensorLog_'+str(sensor_id)+'_1"/> \n <!--{--><!--}-->'    

    if(rdf_file_name=="undefined-data.rdf"):
        print ".................no etl file modification ............."
        return

    with open("./rdf/"+rdf_file_name, "r+") as f:
        lines = [line.replace("<!--{--><!--}-->", s)                
                for line in f]
        f.seek(0)
        f.truncate()
        f.writelines(lines)
    return

