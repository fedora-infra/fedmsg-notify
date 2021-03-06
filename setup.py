from setuptools import setup

requires = [
    'fedmsg',
    'twisted',
    'fmn',
    'requests',
]

setup(
        name="fedmsg-notify",
        version='0.5.9',
        description="Consumer for fedmsg that spits out libnotify desktop notifications",
        author="Luke Macken, Ross Delinger",
        author_email="lmacken@redhat.com",
        url='https://github.com/fedora-infra/fedmsg-notify',
        license='GPLv3',
        install_requires=requires,
        packages=['fedmsg_notify', 'fedmsg_notify.distro_specific'],
        zip_safe=False,
        entry_points={
            'console_scripts':
                ['fedmsg-notify-config = fedmsg_notify.gui:main',
                 'fedmsg-notify-daemon = fedmsg_notify.daemon:main'],
            'moksha.consumer':
                ['fedmsg-notify = fedmsg_notify.daemon:FedmsgNotifyService'],
             },)
