#!/usr/bin/env python
import json
import ssl
import schedule
import time
import threading
import logging
from os import sys, environ

import iotsim.config.iotconfig as cfg
#from iotunit import IOTUnit, IOTUnitFactory
import iotunit

sys.path.append(cfg.mqtt_modules['modulesFolder'])
logging.basicConfig(filename=cfg.logger['logFilePath'], filemode='w', format='%(asctime)s -%(levelname)s- %(message)s', level=cfg.logger['loggerLevel']) 

class ProgramKilled(Exception):
    pass

class IOTContainer:
    
    def __init__(self):
        self.shutdown_flag = threading.Event()
        self.unitMap = { }
        self.scheduler = schedule
        self.scheduler_thread = threading.Thread(name = 'scheduler daemon', target = self.daemon_scheduler)
        self.scheduler_thread.setDaemon(True)
        self.unitList = json.load(open(cfg.mqtt_modules['iotUnitList']))
        self.iot_factory = iotunit.IOTUnitFactory()
        self.init_iot_units()

    def signal_handler(self, signum, frame):
        self.shutdown_flag.set()
        logging.info("shutdown signal received")
        raise ProgramKilled

    def init_iot_units(self):       
        self.unitMap = self.iot_factory.produce_iot_unit(self.unitList, cfg.cfg.mqtt_client, self.scheduler)
        # try:
        #     
        #     for unit in self.unitList:
        #         unit_tmp = IOTUnit(unit, cfg.mqtt_client, self.scheduler)
        #         self.unitMap[unit['name']] = unit_tmp
        # except Exception:
        #    logging.error("init iot units failed")
        #    raise ValueError
        # logging.info("iot units initialized -> %s", self.unitMap.keys())

    def mqtt_threads_start(self):
        self.iot_factory.start_iot_units(self.unitMap)
        # for unit in self.unitMap.values():
        #     unit.start_mqtt_loop()
        # logging.info("clients loop started")
    
    def mqtt_threads_stop(self):
        for unit in self.unitMap.values():
            unit.stop_mqtt_loop()
        logging.info("clients loop stopped")

    def daemon_scheduler(self):
        while not self.shutdown_flag.is_set():
            self.scheduler.run_pending()
            time.sleep(0.5)
        logging.info("scheduler daemon clean shutdown")
        self.scheduler.clear()
        logging.info("scheduler stopped")
      
    def run(self):
        logging.info("starting iot container")
        self.scheduler_thread.start()
        self.mqtt_threads_start()
    
    def shutdown(self):
        logging.info("stopping iot container")
        self.scheduler_thread.join()
        self.mqtt_threads_stop()

