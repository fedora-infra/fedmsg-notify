from paste.deploy.converters import asbool
from fedmsg.consumers import FedmsgConsumer
import fedmsg.text
import logging
import pynotify


log = logging.getLogger("moksha.hub")


class NotifyConsumer(FedmsgConsumer):
    topic = 'org.fedoraproject.*'
    def __init__(self, hub):
        self.hub = hub
        ENABLED = 'fedmsg.consumers.notifyconsumer.enabled'
        if not asbool(hub.config.get(ENABLED, False)):
            log.info(
                'fedmsg.consumers.notifyconsumer disbaled')
        pynotify.init("Fedmsg")

    def consume(self, msg):
        pretty_text = fedmsg.text.msg2repr(msg)
        note = pynotify.Notification(pretty_text)
        note.show()
