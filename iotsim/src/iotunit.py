#!/usr/bin/env python
import paho.mqtt.client as mqtt
import importlib
import ssl
import threading
import logging

from datapublisher import DataPublisher
from datasubscriber import DataSubscriber
import typedefines as types

class IOTUnit:   
    def __init__(self, unit_cfg, mqtt_cfg, scheduler):
        self.client_cfg = mqtt_cfg
        self.name = unit_cfg['name']
        self.registers = unit_cfg['registers']
        self.notifiers = {}
        self.publishers = {}
        self.subscribers = {}      
        if self.client_cfg['use_certificates']:
            self.init_ssl_context()
        self.init_mqtt_connection()
        self.init_data_publishers(scheduler, unit_cfg['publishers'])
        if 'subscribers' in unit_cfg:
            self.init_data_subscribers(unit_cfg['subscribers'])
        self.init_control_loop(scheduler, unit_cfg)
    
    def init_ssl_context(self):
        try:
            self.ssl_context = ssl.create_default_context()
            self.ssl_context.load_verify_locations(self.client_cfg['rootCA'])
            self.ssl_context.load_cert_chain(self.client_cfg['clientCertificate'], self.client_cfg['clientKey'])
        except Exception:
            logging.error('init_ssl_context failed for %s', self.name)
            raise ValueError
        logging.info('ssl_context created for %s', self.name)

    def init_mqtt_connection(self):
        try:
            self.client = mqtt.Client()
            if self.client_cfg['use_certificates']:
                self.client.tls_set_context(self.ssl_context)
            self.client.connect(self.client_cfg['host'], self.client_cfg['port'])
        except Exception:
            logging.error("init_mqtt_connection failed for %s", self.name)
            raise ValueError
        logging.info('unit %(name)s successfully connected to broker %(host)s:%(port)s', {'name':self.name,'host':self.client_cfg['host'],'port':self.client_cfg['port']})
    def init_control_loop(self, scheduler, cfg):
        try:
            control_loop_module = cfg['control_loop_module']
            if control_loop_module is None:
                pass
            else:
                sleep_time = cfg['control_loop_sleep_ms'] 
                self.control_loop_module = importlib.import_module(control_loop_module)
                scheduler.every(sleep_time/1000).seconds.do(self.control_loop_threaded, self.control_loop_module.run)
                logging.info("control loop %(loop)s initialized for unit %(name)s",{'loop':control_loop_module, 'name':self.name})
        except Exception:
            logging.error("failed to initialize control loop for unit %s", self.name)
            raise ValueError

    def init_data_publishers(self, scheduler, pubList):
        try:
            for pub in pubList:
                pub_tmp = DataPublisher(scheduler, pub, self)
                if pub['type'] == types.NOTIFICATION_TYPE:
                   self.notifiers[pub['id']] = pub_tmp
                else:
                   self.publishers[pub['id']] = pub_tmp
        except Exception:
            logging.error("init data publishers failed for unit %s", self.name)
            raise ValueError
        logging.debug("init data publisher -notifiers:%(notifiers)s -publishers:%(publishers)s",{'notifiers': self.notifiers, 'publishers':self.publishers})
    def init_data_subscribers(self, subList):
        try: 
            for sub in subList:
                sub_tmp = DataSubscriber(sub, self)
                self.subscribers[sub['id']] = sub_tmp
        except Exception:
            logging.error("init data subscribers failed for unit %s", self.name)
            raise ValueError
        logging.debug("init data subscribers -subscribers:%s", self.subscribers)
    
    def get_register_value(self, key):
        return self.registers[key]
    
    def set_register_value(self, key, value):
        logging.debug("setting register %(key)s -> old value:%(oldV)s new value:%(newV)s",{'key':key, 'oldV':self.registers[key], 'newV':value})
        self.registers[key] = value

    def start_mqtt_loop(self):
        self.client.loop_start()
    
    def stop_mqtt_loop(self):
        self.client.loop_stop()
        self.client.disconnect()

    def control_loop_threaded(self, job_func):
        job_thread = threading.Thread(target = job_func, args=(self.registers,))
        job_thread.start()

        
    def process_request_threaded(self, req_func, payload, notifier_name_key):
        req_thread = threading.Thread(target = req_func, args=(self.registers, payload, self.notifiers[notifier_name_key].publish_notification))
        req_thread.start()

class IotUnitFactory:
    def __init__(self) -> None:
        pass