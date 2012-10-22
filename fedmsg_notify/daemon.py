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

import os
import json
import urllib
import logging
import dbus
import dbus.glib
import dbus.service
import moksha.hub
import fedmsg.text
import fedmsg.consumers

from gi.repository import Notify, Gio

log = logging.getLogger('moksha.hub')


class FedmsgNotifyService(dbus.service.Object, fedmsg.consumers.FedmsgConsumer):
    """The Fedmsg Notification Daemon.

    This service is started through DBus activation by calling the
    :meth:`Enable` method, and stopped with :meth:`Disable`.

    This class is not only a DBus service, it is also a Moksha message consumer
    that listens to all messages coming from the Fedora Infrastructure. Moksha
    handles automatically connecting to the remote message hub, subscribing to
    all topics, and calling our :meth:`consume` method with each decoded
    message.

    """
    topic = 'org.fedoraproject.*'
    config_key = 'fedmsg.consumers.notifyconsumer.enabled'
    bus_name = 'org.fedoraproject.fedmsg.notify'
    filters = []  # A list of regex filters from the fedmsg text processors
    _object_path = '/%s' % bus_name.replace('.', '/')
    _icon_cache = {}

    __name__ = "FedmsgNotifyService"

    def __call__(self, hub):
        """ This is a silly hack to help us bridge the gap between
        moksha-land and dbus-land.
        """
        return self

    def __init__(self):
        self.connect_signal_handlers()
        self.cfg = fedmsg.config.load_config(None, [])
        moksha_options = {
            self.config_key: True,
            "zmq_subscribe_endpoints": ','.join(
                ','.join(bunch) for bunch in
                self.cfg['endpoints'].values()
            ),
        }
        self.cfg.update(moksha_options)

        moksha.hub.setup_logger(verbose=True)

        # Despite what fedmsg.config might say about what consumers are enabled
        # and which are not, we're only going to let the central moksha hub know
        # about *our* consumer.  By specifying this here, it won't even check
        # the entry-points list.
        consumers, prods = [self], []
        moksha.hub._hub = moksha.hub.CentralMokshaHub(self.cfg, consumers,
                                                      prods)

        fedmsg.consumers.FedmsgConsumer.__init__(self, moksha.hub._hub)

        self.session_bus = dbus.SessionBus()
        bus_name = dbus.service.BusName(self.bus_name, bus=self.session_bus)
        dbus.service.Object.__init__(self, bus_name, self._object_path)

        self.settings_changed(self.settings, 'enabled-filters')

        Notify.init("fedmsg")
        Notify.Notification.new("fedmsg", "activated", "").show()

    def connect_signal_handlers(self):
        self.settings = Gio.Settings.new(self.bus_name)
        self.setting_conn = self.settings.connect(
            'changed::enabled-filters', self.settings_changed)

    def settings_changed(self, settings, key):
        log.info('Settings changed. Reloading filters.')
        services = json.loads(settings.get_string(key))
        filters = []
        for processor in fedmsg.text.processors:
            if processor.__name__ in services:
                filters.append(processor.__prefix__)
        self.filters = filters

    def consume(self, msg):
        body, topic = msg.get('body'), msg.get('topic')
        for filter in self.filters:
            if filter.match(topic):
                break
        else:
            log.debug("Message to %s didn't match filters" % topic)
            return
        pretty_text = fedmsg.text.msg2repr(body, **self.cfg)
        log.debug(pretty_text)
        title = fedmsg.text.msg2title(body, **self.cfg)
        subtitle = fedmsg.text.msg2subtitle(body, **self.cfg)
        link = fedmsg.text.msg2link(body, **self.cfg)
        icon = self.get_icon(fedmsg.text.msg2icon(body, **self.cfg))
        secondary_icon = self.get_icon(
            fedmsg.text.msg2secondary_icon(body, **self.cfg))
        note = Notify.Notification.new(title, subtitle + ' ' + link, icon)
        if secondary_icon:
            note.set_hint_string('image-path', secondary_icon)
        note.show()

    def get_icon(self, icon):
        if icon:
            icon_file = self._icon_cache.get(icon)
            if not icon_file:
                log.debug('Downloading icon: %s' % icon)
                icon_file, headers = urllib.urlretrieve(icon)
                self._icon_cache[icon] = icon_file
            icon = icon_file
        return icon

    @dbus.service.method(bus_name)
    def Enable(self, *args, **kw):
        """ A noop method called by the gui to load this service """

    @dbus.service.method(bus_name)
    def Disable(self, *args, **kw):
        for icon, filename in self._icon_cache.items():
            try:
                os.unlink(filename)
            except OSError:
                pass
        self.hub.close()
        Notify.Notification.new("fedmsg", "deactivated", "").show()
        reactor.stop()


def main():
    FedmsgNotifyService()
    reactor.run()

if __name__ == '__main__':
    main()
