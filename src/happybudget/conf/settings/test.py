"""
Settings configuration file for test environment.
"""
import logging

from happybudget.conf import config, Environments

from .base import LOGGING, REST_FRAMEWORK
from .base import *  # noqa
from .db import postgres_db, sqlite_db, DATABASE_USER


DEBUG = True
ENVIRONMENT = Environments.TEST
ALLOWED_HOSTS = ['testserver']
TIME_ZONE = 'UTC'

EMAIL_ENABLED = False

APP_DOMAIN = 'testserver/'
APP_URL = 'http://%s' % APP_DOMAIN

WAITLIST_ENABLED = False

# Eventually we should configure these for a temporary test directory.
STATICFILES_STORAGE = None
DEFAULT_FILE_STORAGE = 'happybudget.app.io.storages.LocalStorage'

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

TEST_DATABASE_NAME = config(
    name='TEST_DATABASE_NAME',
    default='postgres_test_happybudget'
)
TEST_DATABASE_USER = config(
    name='TEST_DATABASE_USER',
    default=f'test_{DATABASE_USER}'
)
TEST_DATABASE_PASSWORD = config(
    name='TEST_DATABASE_USER',
    default=''
)
TEST_DATABASE_HOST = config(
    name='TEST_DATABASE_HOST',
    default='localhost'
)
TEST_DATABASE_PORT = config(
    name='TEST_DATABASE_PORT',
    default='5432'
)

# We do not include in the set of DATABASES until it is designated to be used
# by specific tests.
TEST_POSTGRES_DB = postgres_db(
    NAME=TEST_DATABASE_NAME,
    USER=TEST_DATABASE_USER,
    HOST=TEST_DATABASE_HOST,
    PASSWORD="",
    PORT=TEST_DATABASE_PORT
)

DATABASES = {'default': sqlite_db("test.sqlite3")}

# The cache should always be disabled by default, but overridden on a test by
# test basis.
CACHE_ENABLED = False

# Even though the cache is disabled by default, there are tests that test the
# cacheing behavior.  In these tests, we want to ensure that we are using the
# DatabaseCache.  For an explanation of why we use the DatabaseCache, see the
# documentation in regard to :obj:`happybudget.app.cache.endpoint_cache`.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'cache_table',
    }
}
