import os
from logging.config import dictConfig

from celery import Celery
from celery.signals import setup_logging

import django


os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'happybudget.conf.settings.local'
)

django.setup()

app = Celery('happybudget')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))


@setup_logging.connect
def config_loggers(*args, **kwargs):
    # pylint: disable=import-outside-toplevel
    from django.conf import settings
    dictConfig(settings.LOGGING)


@app.task
def say_hello():
    print('Hello, World!')


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # pylint: disable=import-outside-toplevel
    from happybudget.app.group.tasks import find_and_delete_empty_groups
    sender.add_periodic_task(
        60.0 * 5.0,  # Every 5 minutes
        find_and_delete_empty_groups.s(),
        name='Find and delete empty groups.'
    )
