"""
Settings configuration file for dev environment.
"""
from greenbudget.conf import Environments, config

from .base import *  # noqa

DEBUG = True
EMAIL_ENABLED = True
ENVIRONMENT = Environments.DEV

APP_DOMAIN = '127.0.0.1:3000'
APP_URL = 'http://%s' % APP_DOMAIN
APP_V1_URL = os.path.join(APP_URL, "v1")

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_DOMAIN = "127.0.0.1"
JWT_COOKIE_SECURE = False
JWT_COOKIE_DOMAIN = '127.0.0.1'
SESSION_COOKIE_DOMAIN = '127.0.0.1'

CSRF_TRUSTED_ORIGINS = [
    '127.0.0.1',
]
ALLOWED_HOSTS = [
    '127.0.0.1',
]