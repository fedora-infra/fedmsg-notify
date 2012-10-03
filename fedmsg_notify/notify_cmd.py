from fedmsg.commands import command

extra_args = []
from notify_consumer import NotifyConsumer
@command(name='fedbadges-notify', extra_args=extra_args, daemonizable=True)
def notify(**kw):
    """
    Send out desktop notifications over zmq
    """

    moksha_options = dict(
            zmq_subscribe_endpoints=','.join(
                ','.join(bunch) for bunch in kw['endpoints'].values()),
            )
    kw.update(moksha_options)
    kw['fedmsg.consumers.notifyconsumer.enabled'] = True

    from moksha.hub import main
    main(options=kw, consumers=[NotifyConsumer])
