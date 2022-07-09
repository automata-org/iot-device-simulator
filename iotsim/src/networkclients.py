#!/usr/bin/env python
import generated_parameters as params
import paho.mqtt.client as mqtt
from threading import Lock
from enum import Enum
import logging
import ssl


class SingletonMeta(type):
    _instances = {}
    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):

        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


class Client(metaclass=SingletonMeta):
    _lock: Lock = Lock()

    def __init__(self, client_parameters) -> None:
        self._init_client(client_parameters)

    @property
    def get_client(self):
        with self._lock:
            return self._client

    def start(self):
        with self._lock:
            self._start()

    def stop(self):
        with self._lock:
            self._stop()

    def _start(self):
        raise Exception("Not Implemented")

    def _stop(self):
        raise Exception("Not Implemented")

    def _init_client(self, client_cfg):
        raise Exception("Not Implemented")


class MQTTClient(Client):
    def __init__(self, client_parameters) -> None:
        self._init_client(client_parameters)

    def _start(self):
        self._client.loop_start()

    def _stop(self):
        self._client.loop_stop()
        self._client.disconnect()

    def _init_client(self, client_cfg):
        self.name = client_cfg.GetId().Get()
        self._init_mqtt_client(client_cfg)

    def _init_mqtt_client(self, client_cfg):
        try:
            self._client = mqtt.Client(client_id=client_cfg.GetId().Get())
            if client_cfg.GetRootCa().Get() != "":
                self._init_ssl_context(client_cfg=client_cfg)
                self._client.tls_set_context(self.ssl_context)
            self._client.connect(client_cfg.GetHost().Get(),
                                 client_cfg.GetPort().Get())
        except Exception:
            logging.error("init_mqtt_connection failed for %s", self.name)
            raise ValueError
        logging.info('client %(name)s successfully connected to broker %(host)s:%(port)s', {
                     'name': self.name, 'host': client_cfg.GetHost().Get(), 'port': client_cfg.GetPort().Get()})

    def _init_ssl_context(self, client_cfg):
        try:
            self.ssl_context = ssl.create_default_context()
            self.ssl_context.load_verify_locations(
                client_cfg.GetRootCa().Get())
            self.ssl_context.load_cert_chain(
                client_cfg.GetClientCertificate().Get(), client_cfg.GetClientKey().Get())
        except Exception:
            logging.error('init_ssl_context failed for %s',
                          client_cfg.GetId().Get())
            raise ValueError
        logging.info('ssl_context created for %s', client_cfg.GetId().Get())


class ClientType(Enum):
    mqtt = 0
    none = -1


_nameToClientType = {
    'mqtt': ClientType.mqtt
}


def GetType(string):
    if string in _nameToClientType.keys():
        return _nameToClientType[string]
    else:
        return ClientType.none


class ClientBuilder:
    def __init__(self) -> None:
        pass

    @staticmethod
    def build(client_parameters):
        if GetType(client_parameters.GetType().Get()) == ClientType.mqtt:
            client = MQTTClient(client_parameters=client_parameters)
            return client
        else:
            logging.error("Client type %s not supported",
                          client_parameters.GetType().Get())
            raise ValueError("only mqtt client type supported")
