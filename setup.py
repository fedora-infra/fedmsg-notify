from setuptools import setup

requires = [
        'fedmsg',
        'pyzmq-static',]
try:
    import pynotify
except:
    print "Please install the libnotify python bindings"
    exit()

setup(
        name="fedmsg-notify-consumer",
        verion='0.1.0',
        description="Consumer for fedmsg that spits out libnotify desktop notifications",
        author="Ross Delinger",
        author_email="rossdylan@csh.rit.edu",
        install_requires=requires,
        packages=['fedmsg_notify_consumer'],
        zip_safe=False,
        entry_points={
            'console_scripts':
                ['fedmsg-notify=fedmsg_notify_consumer.notify_cmd:notify'],
            'moksha.consumer':
                ['fedmsg-notify=fedmsg_notify_consumer.notify_consumer:NotifyConsumer'],
             },)


