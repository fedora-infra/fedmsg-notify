from setuptools import setup

requires = [
    'fedmsg',
    'pyzmq-static',
]

try:
    from gi.repository import Notify
except:
    print "Please install the gobject introspection libraries"
    exit()

setup(
        name="fedmsg-notify",
        verion='0.2.0',
        description="Consumer for fedmsg that spits out libnotify desktop notifications",
        author="Luke Macken, Ross Delinger",
        author_email="lmacken@redhat.com",
        install_requires=requires,
        packages=['fedmsg_notify'],
        zip_safe=False,
        entry_points={
            'console_scripts':
                ['fedmsg-notify-config = fedmsg_notify.gui:main',
                 'fedmsg-notify-daemon = fedmsg_notify.daemon:main'],
            'moksha.consumer':
                ['fedmsg-notify = fedmsg_notify.daemon:FedmsgNotifyService'],
             },)
