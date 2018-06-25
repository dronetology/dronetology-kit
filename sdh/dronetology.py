#!/usr/bin/env python
import os
import sys
import time
import logging
import subprocess
import shutil
import signal
import datetime

#ok-----
#from drone.mavlink import mavlink

def signal_handler(signal, frame):
    print('DRONETOLOGY: You pressed Ctrl+C!')
    logging.debug('DRONETOLOGY: You pressed Ctrl+C!')
    time.sleep(2) 
    os.system('pkill python')
    sys.exit(0)


logging.basicConfig(format='%(asctime)s %(message)s', filename='dronetology.log',level=logging.DEBUG)
signal.signal(signal.SIGINT, signal_handler)

print("dronetology-kit SDH ....starting....................."+str(datetime.datetime.now()))
logging.debug("dronetology-kit SDH ....starting....................."+str(datetime.datetime.now()))

if(sys.argv[1]):
    logging.debug('......running flight type: %s', sys.argv[1])
    flight_type=sys.argv[1]
else:
    logging.debug('......running default flight type: isa1')
    flight_type="isa1"

dronetology_path=os.path.dirname(os.path.abspath(__file__))

subprocess.Popen( dronetology_path+'/dronetology/bin/clean_queue.py', shell=True)

logging.debug("dronetology-kit SDH ....queue cleanned.....................")
time.sleep(2) 

##copy sensor rdf
shutil.copy2('./dronetology/init/dsf-data.rdf', './dronetology/bin/dsf-data.rdf')
shutil.copy2('./dronetology/init/isa1-data.rdf', './dronetology/bin/isa1-data.rdf')

if(flight_type=="isa1"):
    commands = [
    dronetology_path+'/input/read_sensor_data.py',
    dronetology_path+'/dronetology/bin/etl.py',
    dronetology_path+'/dronetology/bin/dronetology_isa1.py',
    dronetology_path+'/result/result_manager.py',    
    ]

if(flight_type=="dsf"):
    commands = [
    dronetology_path+'/input/read_sensor_data.py',
    dronetology_path+'/dronetology/bin/etl.py',
    dronetology_path+'/dronetology/bin/dronetology_dsf.py',  
    dronetology_path+'/result/result_manager.py',      
    ]

if(flight_type=="psa"):
    commands = [
    dronetology_path+'/dronetology/bin/dronetology_psa.py',    
    ]


# run in parallel
processes = [subprocess.Popen(cmd, shell=True) for cmd in commands]
# do other things here..
# wait for completion
print("dronetology-kit SDH ....started.....................")
for p in processes: p.wait()
    