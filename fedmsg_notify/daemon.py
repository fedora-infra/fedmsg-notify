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
from twisted.web.client import downloadPage
from twisted.internet import  defer

import os
import json
import uuid
import logging
import dbus
import dbus.glib
import dbus.service
import moksha.hub
import fedmsg.text
import fedmsg.consumers

from gi.repository import Notify, Gio

from filters import get_enabled_filters, filters as all_filters

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
    msg_received_signal = 'org.fedoraproject.fedmsg.notify.MessageReceived'
    service_filters = []  # A list of regex filters from the fedmsg text processors
    enabled = False
    emit_dbus_signals = None  # Allow us to proxy fedmsg to dbus
    enabled_filters = []
    filters = []

    _icon_cache = {}
    _object_path = '/%s' % bus_name.replace('.', '/')
    __name__ = "FedmsgNotifyService"

    def __call__(self, hub):
        """ This is a silly hack to help us bridge the gap between
        moksha-land and dbus-land.
        """
        return self

    def __init__(self):
        moksha.hub.setup_logger(verbose=True)
        self.settings = Gio.Settings.new(self.bus_name)
        self.emit_dbus_signals = self.settings.get_boolean('emit-dbus-signals')
        if not self.settings.get_boolean('enabled'):
            log.info('Disabled via %r configuration, exiting...' %
                     self.config_key)
            return

        self.session_bus = dbus.SessionBus()
        if self.session_bus.name_has_owner(self.bus_name):
            log.info('Daemon already running. Exiting...')
            return

        self.cache_dir = os.path.expanduser('~/.cache/fedmsg-notify')
        if not os.path.isdir(self.cache_dir):
            os.makedirs(self.cache_dir)

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

        fedmsg.text.make_processors(**self.cfg)
        self.settings_changed(self.settings, 'enabled-filters')

        # Despite what fedmsg.config might say about what consumers are enabled
        # and which are not, we're only going to let the central moksha hub know
        # about *our* consumer.  By specifying this here, it won't even check
        # the entry-points list.
        consumers, prods = [self], []
        moksha.hub._hub = moksha.hub.CentralMokshaHub(self.cfg, consumers,
                                                      prods)

        fedmsg.consumers.FedmsgConsumer.__init__(self, moksha.hub._hub)

        bus_name = dbus.service.BusName(self.bus_name, bus=self.session_bus)
        dbus.service.Object.__init__(self, bus_name, self._object_path)

        Notify.init("fedmsg")
        Notify.Notification.new("fedmsg", "activated", "").show()
        self.enabled = True

    def connect_signal_handlers(self):
        self.setting_conn = self.settings.connect(
            'changed::enabled-filters', self.settings_changed)
        self.settings.connect('changed::emit-dbus-signals',
                              self.settings_changed)
        self.settings.connect('changed::filter-settings',
                              self.settings_changed)

    def settings_changed(self, settings, key):
        self.enabled_filters = get_enabled_filters(self.settings)
        if key == 'enabled-filters':
            log.debug('Reloading filter settings')
            self.service_filters = [processor.__prefix__
                                    for processor in fedmsg.text.processors
                                    if processor.__name__ in self.enabled_filters]

            filter_settings = json.loads(self.settings.get_string('filter-settings'))
            enabled = [filter.__class__.__name__ for filter in self.filters]
            for filter in all_filters:
                name = filter.__name__
                # Remove any filters that were just disabled
                if name in enabled and name not in self.enabled_filters:
                    log.debug('Removing filter: %s' % name)
                    for loaded_filter in self.filters:
                        if loaded_filter.__class__.__name__ == name:
                            self.filters.remove(loaded_filter)
                # Initialize any filters that were just enabled
                if name not in enabled and name in self.enabled_filters:
                    log.debug('Initializing filter: %s' % name)
                    self.filters.append(filter(filter_settings.get(name, '')))
        elif key == 'filter-settings':
            # We don't want to re-initialize all of our filters here, because
            # this could happen for every keystroke the user types in a text
            # entry. Instead, we do the initialization whenever the list of
            # enabled filters changes.
            pass
        elif key == 'emit-dbus-signals':
            self.emit_dbus_signals = settings.get_boolean(key)
        else:
            log.warn('Unknown setting changed: %s' % key)

    def consume(self, msg):
        """ Called by fedmsg (Moksha) with each message as they arrive """
        body, topic = msg.get('body'), msg.get('topic')
        processor = fedmsg.text.msg2processor(msg)
        for filter in self.filters:
            if filter.match(body, processor):
                log.debug('Matched topic %s with %s' % (topic, filter))
                break
        else:
            for filter in self.service_filters:
                if filter.match(topic):
                    log.debug('Matched topic %s with %s' % (topic, filter.pattern))
                    break
            else:
                log.debug("Message to %s didn't match filters" % topic)
                return

        if self.emit_dbus_signals:
            self.MessageReceived(topic, json.dumps(body))

        self.notify(msg)

    @dbus.service.signal(dbus_interface=bus_name, signature='ss')
    def MessageReceived(self, topic, body):
        log.debug('Sending dbus signal to %s' % self.msg_received_signal)

    def notify(self, msg):
        d = self.fetch_icons(msg)
        d.addCallbacks(self.display_notification, errback=log.error,
                       callbackArgs=(msg['body'],))

    def display_notification(self, results, body, *args, **kw):
        pretty_text = fedmsg.text.msg2repr(body, **self.cfg)
        log.debug(pretty_text)
        title = fedmsg.text.msg2title(body, **self.cfg) or ''
        subtitle = fedmsg.text.msg2subtitle(body, **self.cfg) or ''
        link = fedmsg.text.msg2link(body, **self.cfg) or ''
        icon = self._icon_cache.get(fedmsg.text.msg2icon(body, **self.cfg))
        secondary_icon = self._icon_cache.get(
                fedmsg.text.msg2secondary_icon(body, **self.cfg))

        note = Notify.Notification.new(title, subtitle + ' ' + link, icon)
        if secondary_icon:
            note.set_hint_string('image-path', secondary_icon)
        note.show()

    def fetch_icons(self, msg):
        icons = []
        body = msg.get('body')
        icon = fedmsg.text.msg2icon(body, **self.cfg)
        if icon:
            icons.append(self.get_icon(icon))
        secondary_icon = fedmsg.text.msg2secondary_icon(body, **self.cfg)
        if secondary_icon:
            icons.append(self.get_icon(secondary_icon))
        return defer.DeferredList(icons)

    def get_icon(self, icon):
        icon_file = self._icon_cache.get(icon)
        if not icon_file:
            icon_id = str(uuid.uuid5(uuid.NAMESPACE_URL, icon))
            filename = os.path.join(self.cache_dir, icon_id)
            if not os.path.exists(filename):
                log.debug('Downloading icon: %s' % icon)
                d = downloadPage(icon, filename)
                d.addCallbacks(self.cache_icon, errback=log.error,
                               callbackArgs=(icon, filename))
                return d
            else:
                self._icon_cache[icon] = filename
        d = defer.Deferred()
        d.callback(None)
        return d

    def cache_icon(self, results, icon_url, filename):
        self._icon_cache[icon_url] = filename

    @dbus.service.method(bus_name)
    def Enable(self, *args, **kw):
        """ A noop method called to activate this service over dbus """

    @dbus.service.method(bus_name)
    def Disable(self, *args, **kw):
        self.__del__()

    def __del__(self):
        for icon, filename in self._icon_cache.items():
            try:
                os.unlink(filename)
            except OSError:
                pass
        if not self.enabled:
            return
        self.hub.close()
        Notify.Notification.new("fedmsg", "deactivated", "").show()
        Notify.uninit()
        self.enabled = False
        log.info('Exiting...')
        reactor.stop()


def main():
    service = FedmsgNotifyService()
    if service.enabled:
        reactor.run()

if __name__ == '__main__':
    main()
