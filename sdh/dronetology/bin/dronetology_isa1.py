#!/usr/bin/env python
import os
import time
import subprocess
import logging
import re

logging.basicConfig(format='%(asctime)s %(message)s', filename='dronetology.log',level=logging.DEBUG)

# 3rd party modules
import posix_ipc

# Create the message queue.
try:
    mq = posix_ipc.MessageQueue("/RESULT_QUEUE", posix_ipc.O_CREX)
except posix_ipc.ExistentialError:
    mq = posix_ipc.MessageQueue("/RESULT_QUEUE")

sparql_path=os.path.dirname(os.path.abspath(__file__))

print 'INFERENCE MODULE: starting ISA1 flight type................'
logging.debug( 'INFERENCE MODULE: starting ISA1 flight type.............')

waypoint_id=2

while 1:
    
    result = subprocess.check_output([sparql_path+'/sparql','--data='+sparql_path+'/isa1-data.rdf', '--query='+sparql_path+'/isa1-w'+str(waypoint_id)+'.spql', '--graph='+sparql_path+'/dronetology-sdh.owl'])
    a =result.find("continue")
    b =result.find("avoid")

    print(result)

  
    if (b>0):
        print("INFERENCE MODULE: ISA1 AVOID next waypoint "+str(waypoint_id))
        logging.debug("INFERENCE MODULE: ISA1 AVOID next waypoint "+str(waypoint_id))

        b=result.find("=============================================")
        bb=result.find("|", b)
        c=result.find("-----------------", b)
        
        pattern = r'"([0-9_\./\\-]*)"'
        
        m = re.findall(pattern, result[bb:c])

        if(waypoint_id==2):
            waypoint_id=3
            print("INFERENCE MODULE: ISA1 flight to ||"+m[0]+"|"+m[1])
            logging.debug("INFERENCE MODULE: ISA1 flight to ||"+m[0]+"|"+m[1])
            mq.send("AVOID_NEXT_WAYPOINT||"+m[0]+"|"+m[1])
        else:
            print("INFERENCE MODULE: ISA1 flight ..........END")
            logging.debug("INFERENCE MODULE: ISA1 flight.............. END")
            mq.send("END_ISA1")
    else:
        print("INFERENCE MODULE: ISA1 continue to next waypoint "+str(waypoint_id))
        logging.debug("INFERENCE MODULE: ISA1 continue to next waypoint "+str(waypoint_id))

    time.sleep(2)

