#!/usr/bin/env python
import os
import sys
import time
import logging
import subprocess
import shutil
import signal
import datetime

# 3rd party modules
import posix_ipc


def signal_handler(signal, frame):
    print('DRONETOLOGY: You pressed Ctrl+C!')
    logging.debug('DRONETOLOGY: You pressed Ctrl+C!')
    time.sleep(2) 
    os.system('pkill python')
    sys.exit(0)


logging.basicConfig(format='%(asctime)s %(message)s', filename='./log/dronetology.log',level=logging.DEBUG)
signal.signal(signal.SIGINT, signal_handler)


dronetology_path=os.path.dirname(os.path.abspath(__file__))

subprocess.Popen( dronetology_path+'/clean_queue.py', shell=True)

logging.debug("dronetology-kit SDH ....queue cleanned.....................")
time.sleep(2)

# Create the message queue.
try:
    mqs = posix_ipc.MessageQueue("/FLIGHT_TYPE_QUEUE", posix_ipc.O_CREX)
except posix_ipc.ExistentialError:
    print("dronetology-kit SDH ....error..queue /FLIGHT_TYPE_QUEUE....................")
    mqs = posix_ipc.MessageQueue("/FLIGHT_TYPE_QUEUE")



print("dronetology-kit SDH ....starting....................."+str(datetime.datetime.now()))
logging.debug("dronetology-kit SDH ....starting....................."+str(datetime.datetime.now()))

if(sys.argv[1] and sys.argv[2]):
    logging.debug('......running flight type: %s', sys.argv[1]) 
    flight_mode = str(sys.argv[1])   
    flight_type = str(sys.argv[2])
    flight_plan = str(sys.argv[3])
    mqs.send(flight_mode+"|"+flight_type+"|"+flight_plan)
else:
    logging.debug('......running default flight type: isa1')
    flight_type="isa1"

##copy sensor rdf


if (flight_mode.find("debug")>-1):
    print "debug sensors python.........................."
    sensor_py="read_sensor_data_debug.py"
    
else:
    sensor_py="read_sensor_data.py"    


commands=None

if(flight_type=="isa1"):

    shutil.copy2('./rdf/init/isa1-wsn1-data.rdf', './rdf/isa1-wsn1-data.rdf')
    shutil.copy2('./rdf/init/isa1-wsn2-data.rdf', './rdf/isa1-wsn2-data.rdf')
    shutil.copy2('./rdf/init/isa1-wsn3-data.rdf', './rdf/isa1-wsn3-data.rdf')

    commands = [
    dronetology_path+'/'+sensor_py,
    dronetology_path+'/etl.py',
    dronetology_path+'/isa1_inference.py',
    dronetology_path+'/result_manager.py',    
    ]    

if(flight_type=="dsf"):

    shutil.copy2('./rdf/init/dsf-wsn1-data.rdf', './rdf/dsf-wsn1-data.rdf')
    shutil.copy2('./rdf/init/dsf-wsn2-data.rdf', './rdf/dsf-wsn2-data.rdf')
    shutil.copy2('./rdf/init/dsf-wsn3-data.rdf', './rdf/dsf-wsn3-data.rdf')

    commands = [
    dronetology_path+'/'+sensor_py,
    dronetology_path+'/etl.py',
    dronetology_path+'/dsf_inference.py',  
    dronetology_path+'/result_manager.py',      
    ]
    

if(flight_type=="psa"):

    shutil.copy2('./rdf/init/psa-wsn1-data.rdf', './rdf/psa-wsn1-data.rdf')
    shutil.copy2('./rdf/init/psa-wsn2-data.rdf', './rdf/psa-wsn2-data.rdf')
    shutil.copy2('./rdf/init/psa-wsn3-data.rdf', './rdf/psa-wsn3-data.rdf')

    commands = [
    dronetology_path+'/'+sensor_py,
    dronetology_path+'/etl.py',
    dronetology_path+'/psa_inference.py',  
    dronetology_path+'/result_manager.py',      
    ]

if(flight_type=="bfa"):
    commands = [
    dronetology_path+'/'+sensor_py,        
    dronetology_path+'/result_manager.py',      
    ]

if(flight_type=="test1"):

    commands = [           
    dronetology_path+'./test/test_1.py',      
    ]
    
if(flight_type=="test2"):

    commands = [           
    dronetology_path+'./test/test_2.py',      
    ]

if(flight_type=="sensor"):

    commands = [           
    dronetology_path+'/read_sensor_data_debug.py',      
    ]
    
if(commands is None):
    print("dronetology-kit SDH ....flight type not supported....................."+flight_type)
    sys.exit(0)

# run in parallel
processes = [subprocess.Popen(cmd, shell=True) for cmd in commands]
# do other things here..
# wait for completion
print("dronetology-kit SDH ....started.....................")
for p in processes: p.wait()
    