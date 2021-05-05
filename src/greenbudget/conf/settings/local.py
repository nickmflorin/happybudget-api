"""
Settings configuration file for dev environment.
"""
import os

from greenbudget.conf import Environments

from .base import *  # noqa

DEBUG = True
EMAIL_ENABLED = True
ENVIRONMENT = Environments.LOCAL

APP_DOMAIN = '127.0.0.1:8000'
APP_URL = 'http://%s' % APP_DOMAIN
APP_V1_URL = os.path.join(APP_URL, "v1")

EMAIL_HOST = 'localhost'

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_DOMAIN = "127.0.0.1"
JWT_COOKIE_SECURE = False
JWT_COOKIE_DOMAIN = '127.0.0.1'
SESSION_COOKIE_DOMAIN = '127.0.0.1'

CSRF_TRUSTED_ORIGINS = [
    '127.0.0.1'
]
ALLOWED_HOSTS = [
    '127.0.0.1'
]
# CORS Configuration
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_REGEX_WHITELIST = (
    r'^(https?://)?localhost:?[\d]*?$',
    r'^(https?://)?127.0.0.1:?[\d]*?$'
)

try:
    from .local_overrride import *  # noqa
except ImportError:
    pass