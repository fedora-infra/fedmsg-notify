fedmsg-notify
=============

Subscribing to the [Fedora Infrastructure Messsage Bus](http://fedmsg.com) on the desktop.

![fedmsg-notify](http://lewk.org/img/fedmsg-notify-0-crop.png "Realtime desktop notifications")


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

Running
--------

Once installed the "Fedmsg Notification Configuration" should appear in your
application menu. You can also run `fedmsg-notify-config` by hand, or `python
-m fedmsg_notify.gui` from git.

![fedmsg-notify-config](http://lewk.org/img/fedmsg-notify-config-0.png "fedmsg-notify-config")
![fedmsg-notify-config](http://lewk.org/img/fedmsg-notify-config-1.png "fedmsg-notify-config")

Using notification preferences from the FMN server
--------------------------------------------------

It is possible to retrieve your notification preferences from the [FMN
server](https://apps.fedoraproject.org/notifications/) instead of configuring
them locally. To enable this behavior, run:

```
gsettings set org.fedoraproject.fedmsg.notify use-server-prefs true
gsettings set org.fedoraproject.fedmsg.notify fmn-url https://apps.fedoraproject.org/notifications/api/
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
