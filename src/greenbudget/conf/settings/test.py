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

APP_DOMAIN = 'testserver/'
APP_URL = 'http://%s' % APP_DOMAIN

WAITLIST_ENABLED = False

# Eventually we should configure these for a temporary test directory.
STATICFILES_STORAGE = None
DEFAULT_FILE_STORAGE = 'greenbudget.app.io.storages.LocalStorage'

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

CACHE_ENABLED = False

# Even though the cache is disabled by default, there are tests that test the
# cacheing behavior.  In these tests, we want to ensure that we are using the
# DatabaseCache.  For an explanation of why we use the DatabaseCache, see the
# documentation in regard to :obj:`greenbudget.app.cache.endpoint_cache`.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'cache_table',
    }
}
