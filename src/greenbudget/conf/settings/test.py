"""
Settings configuration file for test environment.
"""
import dj_database_url
import logging

from greenbudget.conf import Environments

from .base import ROOT_DIR, LOGGING, REST_FRAMEWORK
from .base import *  # noqa

DEBUG = True
ENVIRONMENT = Environments.TEST
ALLOWED_HOSTS = ['testserver']
TIME_ZONE = 'UTC'

EMAIL_ENABLED = False
CELERY_ENABLED = False
RATELIMIT_ENABLE = False

# Disable logging in tests
LOGGING['loggers'] = {  # noqa
    '': {
        'handlers': ['null'],
        'level': logging.DEBUG,
        'propagate': False,
    },
}
del LOGGING['root']

# Turn off throttling for tests.
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {}

DATABASES = {
    'default': dj_database_url.parse('sqlite:///%s/test.sqlite3' % ROOT_DIR)
}
DATABASES['default']['ATOMIC_REQUESTS'] = True
