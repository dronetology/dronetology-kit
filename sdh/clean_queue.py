#!/usr/bin/env python
import logging

# 3rd party modules
import posix_ipc

logging.basicConfig(format='%(asctime)s %(message)s', filename='./log/dronetology.log',level=logging.DEBUG)

logging.debug("QUEUE cleanned")

try:
    posix_ipc.unlink_message_queue("/RESULT_QUEUE")
except posix_ipc.ExistentialError:
    logging.info(" No queue exists with the specified name /RESULT_QUEUE......")

try:
    posix_ipc.unlink_message_queue("/INPUT_QUEUE")
except posix_ipc.ExistentialError:
    logging.info(" No queue exists with the specified name /INPUT_QUEUE......")

try:
    posix_ipc.unlink_message_queue("/MISSION_WAYPOINT_QUEUE")
except posix_ipc.ExistentialError:
    logging.info(" No queue exists with the specified name /MISSION_WAYPOINT_QUEUE......")

try:
    posix_ipc.unlink_message_queue("/FLIGHT_TYPE_QUEUE")
except posix_ipc.ExistentialError:
    logging.info(" No queue exists with the specified name /FLIGHT_TYPE_QUEUE......")

try:
    posix_ipc.unlink_message_queue("/UAS_POSITION")
except posix_ipc.ExistentialError:
    logging.info(" No queue exists with the specified name /UAS_POSITION......")

