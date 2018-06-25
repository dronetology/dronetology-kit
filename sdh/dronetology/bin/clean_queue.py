#!/usr/bin/env python
import logging

# 3rd party modules
import posix_ipc

logging.basicConfig(format='%(asctime)s %(message)s', filename='dronetology.log',level=logging.DEBUG)

logging.debug("QUEUE cleanned")

posix_ipc.unlink_message_queue("/RESULT_QUEUE")
posix_ipc.unlink_message_queue("/INPUT_QUEUE")

