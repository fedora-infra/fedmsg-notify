fedmsg-notify
=============

Subscribing to the [Fedora Infrastructure Messsage Bus](http://fedmsg.com) on the desktop.


Features
--------

 * A dbus-activated `fedmsg-notify-daemon` that consumes every message
   from the Fedora Infrastructure Messaging bus.

 * A `fedmsg-notify-config` graphical interface that lets you filter which
   messages to display


Installing
----------

Due to a dependency on Twisted's gtk3reactor, fedmsg-notify is currently
only available on [Fedora 18](https://apps.fedoraproject.org/packages/fedmsg-notify).

```
yum -y install fedmsg-notify
```


Writing applications that consume fedmsg messages through DBus
--------------------------------------------------------------

The `fedmsg-notify-daemon` has the ability to relay messages over DBus. When
enabled, it will trigger a `org.fedoraproject.fedmsg.notify.MessageReceived`
signal upon each message. This behavior can be enabled by running:

```
gsettings set org.fedoraproject.fedmsg.notify emit-dbus-signals true
```

Here is an example of a basic Python program that listens to fedmsg-notify signals over DBus.

```python

import json
import dbus
import dbus.mainloop.glib

from pprint import pprint
from gi.repository import GObject

class FedmsgListener(object):
    """ An example service that listens to fedmsg-notify signals over dbus """

    def __init__(self):
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SessionBus()
        self.bus.add_signal_receiver(self.consume,
                                     signal_name='MessageReceived',
                                     dbus_interface='org.fedoraproject.fedmsg.notify',
                                     path='/org/fedoraproject/fedmsg/notify')

    def consume(self, topic, body):
        body = json.loads(body)
        print(topic)
        pprint(body)


if __name__ == '__main__':
    l = FedmsgListener()
    loop = GObject.MainLoop()
    loop.run()
```
