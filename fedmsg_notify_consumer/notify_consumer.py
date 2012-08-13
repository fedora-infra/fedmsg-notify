from paste.deploy.converters import asbool
from fedmsg.consumers import FedmsgConsumer
import logging
import zmq
import json

log = logging.getLogger("moksha.hub")


class NotifyConsumer(FedmsgConsumer):
    def __init__(self, hub):
        self.hub = hub
        ENABLED = 'fedmsg.consumers.notifyconsumer.enabled'
        if not asbool(hub.config.get(ENABLED, False)):
            log.info(
                'fedmsg.consumers.notifyconsumer disbaled')
        self.context = zmq.Context()
        self.subscribers = self.context.socket(zmq.PUB)
        settings = self.hub.get("notify")

        listen_uri = settings.get(
                'listener_uri',
                'tcp://127.0.0.1:9934')
        self.subscribers.bind(listen_uri)

    def consume(self, msg):
        self.subscribers.send(json.dumps(msg))
