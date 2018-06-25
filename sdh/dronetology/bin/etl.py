#!/usr/bin/env python
import time
import re
import logging


logging.basicConfig(format='%(asctime)s %(message)s', filename='dronetology.log',level=logging.DEBUG)


# 3rd party modules
import posix_ipc

def emptyHarvestedSensor(filename):
    print("empty")
    return

def addHarvestedSensor(filename, sensorId):

    if(sensorId==562):    
        s='<isFlightOf rdf:resource="http://www.dronetology.net/dronetology-sdh.owl#sensorLog_3_1"/> \n <!--{--><!--}-->'
    else:
        s='<isFlightOf rdf:resource="http://www.dronetology.net/dronetology-sdh.owl#sensorLog_2_1"/> \n <!--{--><!--}-->' 
    

    with open(filename, "r+") as f:
        lines = [line.replace("<!--{--><!--}-->", s)                
                for line in f]
        f.seek(0)
        f.truncate()
        f.writelines(lines)
    return




# ..............for testing purposes
# Create the message queue.
try:
    mq = posix_ipc.MessageQueue("/INPUT_QUEUE", posix_ipc.O_CREX)    

except posix_ipc.ExistentialError:
    mq = posix_ipc.MessageQueue("/INPUT_QUEUE")

# ..............for testing purposes
#mq.send("SENSOR ID:562")

#to control max sensor in RDF
harvested_sensor=1

while 1:

    print("ETL MODULE: waiting for a new harvested sensor ........")
    logging.debug("ETL MODULE: waiting for a new harvested sensor .........")

    try:
        s= mq.receive(2)[0]  
        logging.debug("ETL MODULE:Received from queue, new sensor harvested "+s)
        print("ETL MODULE:Received from queue, new sensor harvested "+s)
    except posix_ipc.BusyError: 
        logging.debug("ETL MODULE: queue empty ")
        print("ETL MODULE: queue empty ")   
        s="noSensorHarvested" 

    pattern = r'\d+'
    m = re.findall(pattern, s)  

    if not m:
        logging.debug("ETL MODULE: no sensor harvested ")
        print("ETL MODULE: no sensor harvested ")
    else:
        if(harvested_sensor<3):
            addHarvestedSensor('dsf-data.rdf', int(m[0]))
            addHarvestedSensor('isa1-data.rdf', int(m[0]))
            print("ETL MODULE: harvested sensor added to RDF, waiting for more........."+m[0])
            logging.debug("ETL MODULE: harvested sensor added to RDF, waiting for more........."+m[0])
            harvested_sensor+=1
        else:
            #do no stop --> log others sensors
            print("ETL MODULE: harvested sensor NOT added to RDF, ......."+m[0])
            logging.debug("ETL MODULE: harvested sensor NOT added to RDF, ......."+m[0])
            
    time.sleep(1)