#!/usr/bin/env python
#-*- coding:utf-8 -*-


import sys, os
sys.path.append(os.path.abspath(os.path.join("..")))

from common.Def import INTFTYPE, MSG_HDR_LEN, MSGTYPE
from common.Service import Service
from TSD import TSD
from AutoConnector import WiFiAutoConnector
from IntfOpsDef import WiFiIntfOps
import time
import logging

logging.basicConfig(level=logging.INFO)

def main(*args, **kwargs):

    connector = WiFiAutoConnector()
   
    while not connector.has_connectivity() and not connector.try_to_connect():
        logging.warning("TSD: has no connectivity, will try again after 3s")
        time.sleep(3)

    tsd = TSD(intfops=[WiFiIntfOps()])

    s = Service(1, "Web", "Web", 8080, "tcp")
    
    while tsd.start_service([s]) == False:
        #retry after 3s
        logging.warning("TSD: fail to become hotspot, will try again after 3s")
        time.sleep(3)

    print raw_input("Enter any key to stop service")
    tsd.stop_service()

if __name__ == "__main__":
    main()