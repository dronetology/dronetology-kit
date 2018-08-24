#!/usr/bin/env python
import time
import subprocess
import logging
import os


logging.basicConfig(format='%(asctime)s %(message)s', filename='./log/dronetology.log',level=logging.DEBUG)

# 3rd party modules
import posix_ipc

import imp

inference = imp.load_source('inference', './inference/inference.py')


# Create the message queue.
try:
    mq = posix_ipc.MessageQueue("/RESULT_QUEUE", posix_ipc.O_CREX)
except posix_ipc.ExistentialError:
    mq = posix_ipc.MessageQueue("/RESULT_QUEUE")

try:     
    mqs = posix_ipc.MessageQueue("/FLIGHT_TYPE_QUEUE", posix_ipc.O_CREX)  
except posix_ipc.ExistentialError:   
    mqs = posix_ipc.MessageQueue("/FLIGHT_TYPE_QUEUE")

#blocked until receive flight type
flight_params= mqs.receive()[0] 
#para evitar que se quede vacia
mqs.send(flight_params)


logging.debug("INFERENCE MODULE:  flight params................."+flight_params)
print("INFERENCE MODULE: flight params.............."+flight_params) 


sparql_exec=os.path.abspath("./ext/bin")
sparql_path=os.path.abspath("./sparql")
rdf_path=os.path.abspath("./rdf")
owl_path=os.path.abspath("./owl")

rdf_file_name="undefined-data.rdf"

if(flight_params.find("|1")>-1):    
    rdf_file_name="psa-wsn1-data.rdf"    
if(flight_params.find("|2")>-1):    
    rdf_file_name="psa-wsn2-data.rdf"    
if(flight_params.find("|3")>-1):    
    rdf_file_name="psa-wsn3-data.rdf"

result=inference.sparql_wrapper(rdf_file_name, "psa.spql")

print(result)
#wid del sensor a eliminar  
b =result.find("xsd:int")

if (b>0):
    logging.debug("INFERENCE MODULE: PSA...........DELETE_WAYPOINT ")
    print("INFERENCE MODULE: PSA...........DELETE_WAYPOINT ")
    mq.send("DELETE_WAYPOINT")
else:
    logging.debug("INFERENCE MODULE: PSA...........FLIGHT PLAN OK...... ")
    print("INFERENCE MODULE: PSA...........FLIGHT PLAN OK ")