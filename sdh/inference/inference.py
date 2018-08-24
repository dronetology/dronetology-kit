#!/usr/bin/env python
import time
import logging
import exceptions
import dronekit
import csv
import math
import os
import sys
import subprocess

# Import DroneKit-Python
from dronekit import LocationGlobalRelative

def sparql_wrapper(rdf_file_name, sparql_file_name):

    sparql_exec=os.path.abspath("./ext/bin")
    sparql_path=os.path.abspath("./sparql")
    rdf_path=os.path.abspath("./rdf")
    owl_path=os.path.abspath("./owl")

    result = subprocess.check_output([sparql_exec+'/sparql','--data='+rdf_path+'/'+rdf_file_name, '--query='+sparql_path+'/'+sparql_file_name, '--graph='+owl_path+'/dronetology-sdh.owl'])

    return result




def pending_sensor_latlon(flight_params, sensors_visited):

    #la parada no es que len(sensors_visited)==4

    sparql_exec=os.path.abspath("./ext/bin")
    sparql_path=os.path.abspath("./sparql")
    rdf_path=os.path.abspath("./rdf")
    owl_path=os.path.abspath("./owl")
    

    #join(str(e) for e in sensors_visited)
    print "pending_sensor_latlon..................DSF visited positions of sensors......"+str(len(sensors_visited))
    
    if(flight_params.find("|1")>-1):
        result = subprocess.check_output([sparql_exec+'/sparql','--data='+rdf_path+'/dsf-wsn1-data.rdf', '--query='+sparql_path+'/pending_sensors.spql', '--graph='+owl_path+'/dronetology-sdh.owl'])
    else:
        result = subprocess.check_output([sparql_exec+'/sparql','--data='+rdf_path+'/dsf-wsn2-data.rdf', '--query='+sparql_path+'/pending_sensors.spql', '--graph='+owl_path+'/dronetology-sdh.owl'])
    
    found_sensor=False
    print(result)
    #| "3"^^xsd:int | "42.829943"^^xsd:float | "-1.744440"^^xsd:float |
    #  
    for line in result.splitlines():
        if line.find("^^xsd:int")>-1:
            sensor= line[3:4]
            if sensor in sensors_visited:
                print "pending_sensor_latlon.......already visited...."+sensor
            else:
                #print line
                lat=line[18:27]
                lon=line[43:52]
                found_sensor=True
                sensors_visited.append(sensor)
                print "pending_sensor_latlon..........................should fly to sensor id:"+sensor
                break
    
    if found_sensor:
        return LocationGlobalRelative(float(lat), float(lon), 15)  
    else:
        print "pending_sensor_latlon.................NO pending sensor found .................."
        return None  
