#!/usr/bin/env python
import time
import subprocess
import logging
import os


logging.basicConfig(format='%(asctime)s %(message)s', filename='dronetology.log',level=logging.DEBUG)

# 3rd party modules
import posix_ipc

# Create the message queue.
try:
    mq = posix_ipc.MessageQueue("/RESULT_QUEUE", posix_ipc.O_CREX)
except posix_ipc.ExistentialError:
    mq = posix_ipc.MessageQueue("/RESULT_QUEUE")

print 'INFERENCE MODULE: starting PSA flight type................'
logging.debug( 'INFERENCE MODULE: starting PSA flight type.............')


sparql_path=os.path.dirname(os.path.abspath(__file__))

result = subprocess.check_output([sparql_path+'/sparql','--data='+sparql_path+'/psa-data.rdf', '--query='+sparql_path+'/psa.spql', '--graph='+sparql_path+'/dronetology-sdh.owl'])

print(result)
#wid del sensor a eliminar  
b =result.find("4")

if (b>0):
    logging.debug("INFERENCE MODULE: PSA...........DELETE_WAYPOINT 4")
    print("INFERENCE MODULE: PSA...........DELETE_WAYPOINT 4")
    mq.send("DELETE_WAYPOINT")
else:
    logging.debug("INFERENCE MODULE: PSA...........FLIGHT PLAN OK...... ")
    print("INFERENCE MODULE: PSA...........FLIGHT PLAN OK ")