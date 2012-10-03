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

import sys
import dbus

from gi.repository import Gtk


class FedmsgNotifyConfigWindow(Gtk.ApplicationWindow):
    bus_name = 'org.fedoraproject.fedmsg.notify'
    obj_path = '/org/fedoraproject/fedmsg/notify'

    def __init__(self, app):
        Gtk.Window.__init__(self, title="fedmsg-notify-config", application=app)
        self.set_default_size(300, 100)
        self.set_border_width(10)

        self.bus = dbus.SessionBus()
        running = self.bus.name_has_owner(self.bus_name)

        switch = Gtk.Switch()
        switch.set_active(running)
        switch.connect("notify::active", self.activate_cb)

        label = Gtk.Label()
        label.set_text("Fedmsg Desktop Notifications")

        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.attach(label, 1, 0, 1, 1)
        grid.attach(switch, 0, 0, 1, 1)
        self.add(grid)

    def activate_cb(self, button, active):
        notify_obj = self.bus.get_object(self.bus_name, self.obj_path)
        notify_iface = dbus.Interface(notify_obj, self.bus_name)
        if button.get_active():
            notify_iface.Enable()
        else:
            notify_iface.Disable()


class FedmsgNotifyConfigApp(Gtk.Application):

    def do_activate(self):
        win = FedmsgNotifyConfigWindow(self)
        win.show_all()

    def do_startup(self):
        Gtk.Application.do_startup(self)

if __name__ == '__main__':
    app = FedmsgNotifyConfigApp()
    sys.exit(app.run(sys.argv))
