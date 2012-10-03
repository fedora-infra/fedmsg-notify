#!/usr/bin/env python
# This file is a part of fedmsg-notify.
#
# fedmsg-notify is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# fedmsg-notify is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with fedmsg-notify.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (C) 2012 Red Hat, Inc.
# Author: Luke Macken <lmacken@redhat.com>

from twisted.internet import gtk3reactor
gtk3reactor.install()
from twisted.internet import reactor

import logging
import dbus
import dbus.service
if getattr(dbus, 'version', (0, 0, 0)) >= (0, 41, 0):
    import dbus.glib

import moksha.hub
import fedmsg.text
import fedmsg.consumers
from gi.repository import Notify

log = logging.getLogger('moksha.hub')


class FedmsgNotifyService(dbus.service.Object, fedmsg.consumers.FedmsgConsumer):
    topic = 'org.fedoraproject.*'
    config_key = 'fedmsg.consumers.notifyconsumer.enabled'
    bus_name = 'org.fedoraproject.fedmsg.notify'
    obj_path = '/%s' % bus_name.replace('.', '/')
    endpoint = 'tcp://hub.fedoraproject.org:9940'

    def __init__(self):
        cfg = {'zmq_enabled': True,
               'zmq_subscribe_endpoints': self.endpoint,
               self.config_key: True}
        moksha.hub.setup_logger(verbose=True)
        moksha.hub._hub = moksha.hub.CentralMokshaHub(cfg)
        fedmsg.consumers.FedmsgConsumer.__init__(self, moksha.hub._hub)

        self.session_bus = dbus.SessionBus()
        bus_name = dbus.service.BusName(self.bus_name, bus=self.session_bus)
        dbus.service.Object.__init__(self, bus_name, self.obj_path)

        Notify.init("fedmsg")
        Notify.Notification.new("fedmsg", "activated", "").show()

    def consume(self, msg):
        body, topic = msg.get('body'), msg.get('topic')
        pretty_text = fedmsg.text.msg2repr(body)
        note = Notify.Notification.new("fedmsg", pretty_text, "")
        note.show()

    @dbus.service.method(bus_name)
    def Enable(self, *args, **kw):
        """ A noop method called by the gui to load this service """
        return True

    @dbus.service.method(bus_name)
    def Disable(self, *args, **kw):
        Notify.Notification.new("fedmsg", "deactivated", "").show()
        reactor.stop()
        return True


def main():
    server = FedmsgNotifyService()
    reactor.run()

if __name__ == '__main__':
    main()
