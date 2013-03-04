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

from gi.repository import GObject
from dbus.mainloop.glib import DBusGMainLoop

def consume(topic, body):
    print(topic)
    print(json.loads(body))

DBusGMainLoop(set_as_default=True)
bus = dbus.SessionBus()
bus.add_signal_receiver(consume, signal_name='MessageReceived',
                        dbus_interface='org.fedoraproject.fedmsg.notify',
                        path='/org/fedoraproject/fedmsg/notify')
loop = GObject.MainLoop()
loop.run()
```
