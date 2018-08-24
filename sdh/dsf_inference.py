#!/usr/bin/env python
import time
import subprocess
import re
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

#for dsf-data.rdf usage --> delete form owl: http://www.dronetology.net/dronetology-sdh.owl#droneflight_1


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


rdf_file_name="undefined-data.rdf"

if(flight_params.find("|1")>-1):    
    rdf_file_name="dsf-wsn1-data.rdf"    
if(flight_params.find("|2")>-1):    
    rdf_file_name="dsf-wsn2-data.rdf"    
if(flight_params.find("|3")>-1):    
    rdf_file_name="dsf-wsn3-data.rdf"


print 'INFERENCE MODULE: starting DSF flight type................'
logging.debug( 'INFERENCE MODULE: starting DSF flight type.............')

inference_sent="undefined"

while 1:

    result=inference.sparql_wrapper(rdf_file_name, "dsf.spql")
      
    a =result.find('| 0   | 0   | "0')

    if(result==inference_sent):
        #print "INFERENCE MODULE:......................already sent.............. "+result
        print ""
    else:
        inference_sent=result
        if (a>0):
            #print("INFERENCE MODULE: DSF flight ..........END")
            logging.debug("INFERENCE MODULE: DSF flight.............. END")
            mq.send("END_DSF") 
            print("INFERENCE MODULE:  DSF flight .................INFERENCE END................. ")    
            logging.debug("INFERENCE MODULE: ENDED  ") 
            #si termina y result no esta en el bucle se cuelga pq no le llega el fin
                
        else:
            b=result.find("===========================================")
            bb=result.find("|", b)
            c=result.find("---------------", b)
            
            pattern = r'"([0-9_\./\\-]*)"'        
            m = re.findall(pattern, result[bb:c])

            #print(m)

            centroid_lat=float(m[0])/float(m[2])
            centroid_lon=float(m[1])/float(m[2])
            #print "INFERENCE MODULE: DSF flight ..............NEW_CENTROID...................."+str(centroid_lat)+"|"+str(centroid_lon)
            logging.debug("INFERENCE MODULE: DSF flight ........NEW_CENTROID||"+str(centroid_lat)+"|"+str(centroid_lon))
            mq.send("NEW_CENTROID||"+str(centroid_lat)+"|"+str(centroid_lon) )

    time.sleep(2)

