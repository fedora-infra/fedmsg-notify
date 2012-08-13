from setuptools import setup

requires = [
        'fedmsg',
        'pyzmq-static',]
setup(
        name="fedmsg-notify-consumer",
        verion='0.1.0',
        description="Consumer for fedmsg that sends out notifications to a desktop app",
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


