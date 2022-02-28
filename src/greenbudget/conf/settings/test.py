"""
Settings configuration file for test environment.
"""
import dj_database_url
import logging

from greenbudget.conf import config, Environments
from greenbudget.lib.utils import merge_dicts

from .base import ROOT_DIR, LOGGING, REST_FRAMEWORK, DATABASES
from .base import *  # noqa

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

# Using a postgres test database is not required and the configuration will only
# be used when running certain tests.
TEST_DB = config.multiple(
    NAME={
        'name': 'TEST_DATABASE_NAME',
        'default': 'postgres_test_greenbudget'
    },
    USER={
        'name': 'TEST_DATABASE_USER',
        'default': 'greenbudget'
    },
    HOST={
        'name': 'TEST_DATABASE_HOST',
        'default': 'localhost'
    },
    PORT={
        'name': 'TEST_DATABASE_PORT',
        'default': 5432,
    },
    PASSWORD={
        'name': 'TEST_DATABASE_PASSWORD',
        'default': ''
    }
)

# For the test postgres database, we want the configuration parameters to be
# exactly the same as production except for access level configuration params.
production_default_db = DATABASES["default"]

DATABASES = {
    'default': merge_dicts(
        dj_database_url.parse('sqlite:///%s/test.sqlite3' % ROOT_DIR),
        # Use atomic requests for the test database consistently with how they
        # are used in production.
        ATOMIC_REQUESTS=production_default_db['ATOMIC_REQUESTS']
    ),
    'postgres': merge_dicts(production_default_db,
        NAME=TEST_DB.NAME,
        USER=TEST_DB.USER,
        HOST=TEST_DB.HOST,
        PASSWORD=TEST_DB.PASSWORD,
        PORT=TEST_DB.PORT
    )
}

# The cache should always be disabled by default, but overridden on a test by
# test basis.
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
