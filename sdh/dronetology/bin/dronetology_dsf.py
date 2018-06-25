#!/usr/bin/env python
import time
import subprocess
import re
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

#for dsf-data.rdf usage --> delete form owl: http://www.dronetology.net/dronetology-sdh.owl#droneflight_1


print 'INFERENCE MODULE: starting DSF flight type................'
logging.debug( 'INFERENCE MODULE: starting DSF flight type.............')


sparql_path=os.path.dirname(os.path.abspath(__file__))


while 1:
    result = subprocess.check_output([sparql_path+'/sparql','--data='+sparql_path+'/dsf-data.rdf', '--query='+sparql_path+'/dsf.spql', '--graph='+sparql_path+'/dronetology-sdh.owl'])
    print(result)    
    a =result.find("| 0   | 0   | 0 |")

    if (a>0):
        print("INFERENCE MODULE: DSF flight ..........END")
        logging.debug("INFERENCE MODULE: DSF flight.............. END")
        mq.send("END_DSF")        
    else:
        b=result.find("===========================================")
        bb=result.find("|", b)
        c=result.find("---------------", b)
        
        pattern = r'"([0-9_\./\\-]*)"'        
        m = re.findall(pattern, result[bb:c])

        print(m)
        centroid_lat=float(m[0])/float(m[2])
        centroid_lon=float(m[1])/float(m[2])
        print "INFERENCE MODULE: DSF flight .........NEW_CENTROID||"+str(centroid_lat)+"|"+str(centroid_lon)
        logging.debug("INFERENCE MODULE: DSF flight ........NEW_CENTROID||"+str(centroid_lat)+"|"+str(centroid_lon))
        mq.send("NEW_CENTROID||"+m[0]+"|"+m[1] )

    time.sleep(2)

