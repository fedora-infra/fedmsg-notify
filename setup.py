from setuptools import setup

requires = [
        'fedmsg',
        'zmq-static',]
setup(
        name="fedmsg-notify-consumer",
        verion='0.1.0',
        description="Consumer for fedmsg that sends out notifications to a desktop app",
        author="Ross Delinger",
        author_email="rossdylan@csh.rit.edu",
        install_requires=requires,
        packages=['fedmsg-notify-consumer'],
        zip_safe=False,
        entry_points={
            'console_scripts':
                ['fedmsg-notify=fedmsg-notify-consumer.notify_command:notify'],
            'moksha.consumer':
                ['fedmsg-notify=fedmsg-notify-consumer.notify_consumer:NotifyConsumer'],
             },)

