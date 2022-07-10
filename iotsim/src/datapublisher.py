#!/usr/bin/env python
import threading
import logging
import json
import typedefines as types

class DataPublisher:    
    def __init__(self, scheduler, publisher_cfg, owner):
        self.owner = owner
        self.id = publisher_cfg['id']
        self.register_read_key = publisher_cfg['read']
        self.topic = publisher_cfg['topic']
        self.type = publisher_cfg['type']
        self.register_publisher(scheduler, publisher_cfg)
        
    def register_publisher(self, scheduler, cfg):
        try:
            if self.type == types.PERIODIC_TYPE:       
                self.execution_timer = cfg['cycle_time_ms']
                scheduler.every(self.execution_timer/1000).seconds.do(self.run_threaded, self.publish)
            elif self.type == types.NOTIFICATION_TYPE:
                pass
        except Exception:
            logging.error("register_publisher -> %s failed", self.id)
            raise ValueError
        logging.info("publishing on topic %(topic)s as %(type)s", {'topic': self.topic,'type':self.type})
           
    def run_threaded(self, job_func):
        job_thread = threading.Thread(target = job_func)
        job_thread.start()

    def publish(self):
        payload = self.owner.get_register_value(self.register_read_key)
        self.owner.client.get_client.publish(self.topic, json.dumps(payload))
    
    def publish_notification(self):
        notification_thread = threading.Thread(target = self.publish)
        notification_thread.start()
