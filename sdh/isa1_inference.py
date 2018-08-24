#!/usr/bin/env python
import os
import time
import subprocess
import logging
import re

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
    mqw = posix_ipc.MessageQueue("/MISSION_WAYPOINT_QUEUE", posix_ipc.O_CREX)      
except posix_ipc.ExistentialError:    
    mqw = posix_ipc.MessageQueue("/MISSION_WAYPOINT_QUEUE")  

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
    rdf_file_name="isa1-wsn1-data.rdf"    
if(flight_params.find("|2")>-1):    
    rdf_file_name="isa1-wsn2-data.rdf"    
if(flight_params.find("|3")>-1):    
    rdf_file_name="isa1-wsn3-data.rdf"


print 'INFERENCE MODULE: starting ISA1 flight type................'
logging.debug( 'INFERENCE MODULE: starting ISA1 flight type.............')


#order must be preserved
#waypoint change only with avoid, what if arrived?
#only one change

#W2
sparql_file_name="isa1-w1.spql"
inference_sent="undefined"
next_waypoint="2"

while 1:
    
    #blocked 1s until receive next waypoint
    try:
        next_waypoint= mqw.receive(1)[0] 
        if(next_waypoint=="1" or next_waypoint=="2"):
            #W2
            sparql_file_name="isa1-w1.spql"
            #logging.debug("INFERENCE MODULE: ISA1......next waypoint...W2........"+str(sparql_file_name))
            #print("INFERENCE MODULE: ISA1......next waypoint....W2..."+str(sparql_file_name) )
        elif(next_waypoint=="3"):
            sparql_file_name="isa1-w2.spql"
            #logging.debug("INFERENCE MODULE: ISA1......next waypoint...W3........"+str(sparql_file_name) )
            #print("INFERENCE MODULE: ISA1......next waypoint....W3...."+str(sparql_file_name) ) 
        else:            
            logging.debug("INFERENCE MODULE: ENDED  W4 ") 
            print("INFERENCE MODULE:  ISA1 flight ENDED ...............................W4.................... ")    
            mq.send("END_ISA1")  
            break           
        

    except posix_ipc.BusyError: 
        logging.debug("INFERENCE MODULE: ISA1.....waypoint queue empty..........")
        #print("INFERENCE MODULE: ISA1.......waypoint queue empty........")     

    #print("INFERENCE MODULE: ISA1 checking next waypoint "+str(waypoint_id))
    #logging.debug("INFERENCE MODULE: ISA1 checking next waypoint "+str(waypoint_id))

    result=inference.sparql_wrapper(rdf_file_name, sparql_file_name)
        
    a =result.find("continue")
    b =result.find("avoid")
    print result

    if(result==inference_sent):
        #print "INFERENCE MODULE:......................already sent "+result
        print ""
    else:
        inference_sent=result        
        if (b>0):
            print("INFERENCE MODULE: .................ISA1 AVOID waypoint "+str(next_waypoint))
            logging.debug("INFERENCE MODULE: ISA1 AVOID waypoint "+str(next_waypoint))

            b=result.find("=============================================")
            bb=result.find("|", b)
            c=result.find("-----------------", b)
            
            pattern = r'"([0-9_\./\\-]*)"'
            
            m = re.findall(pattern, result[bb:c])

            if(next_waypoint=="4"):
                #print("INFERENCE MODULE: ISA1 flight to home ")
                logging.debug("INFERENCE MODULE: ISA1 flight ....avoid W3, flight to W4 and END ")
                print("INFERENCE MODULE:  ISA1 flight ....................AVOID W3, flight to W4 and END  ")    
                mq.send("END_ISA1")
            else:
                #print("INFERENCE MODULE: ISA1 flight to next waypoint "+str(waypoint_id+1))
                logging.debug("INFERENCE MODULE: ISA1 flight avoid next waypoint .............."+str(next_waypoint))
                #print("INFERENCE MODULE: ISA1 flight to ||"+m[0]+"|"+m[1])
                logging.debug("INFERENCE MODULE: AVOID_NEXT_WAYPOINT ||"+str(next_waypoint))
                #mq.send("AVOID_NEXT_WAYPOINT||"+m[0]+"|"+m[1])
                mq.send("AVOID_NEXT_WAYPOINT||"+str(next_waypoint))
        
        else:
            #print("INFERENCE MODULE: ISA1 continue to waypoint "+str(waypoint_id))
            logging.debug("INFERENCE MODULE: ISA1 continue to waypoint "+str(next_waypoint))

    time.sleep(2)

