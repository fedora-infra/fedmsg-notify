from paste.deploy.converters import asbool
from fedmsg.consumers import FedmsgConsumer
import fedmsg.text
import logging
from gi.repository import Notify

log = logging.getLogger("moksha.hub")


class NotifyConsumer(FedmsgConsumer):
    topic = 'org.fedoraproject.*'
    config_key = 'fedmsg.consumers.notifyconsumer.enabled'
    def __init__(self, hub):
        self.hub = hub

        ENABLED = self.config_key
        if not asbool(hub.config.get(ENABLED, False)):
            log.info(
                'fedmsg.consumers.notifyconsumer disbaled')
        Notify.init("Fedmsg")
        return super(NotifyConsumer, self).__init__(hub)

    def consume(self, msg):
        body, topic = msg.get('body'), msg.get('topic')
        pretty_text = fedmsg.text.msg2repr(body)
        print pretty_text
        note = Notify.Notification.new("Fedmsg", pretty_text, "")
        note.show()
