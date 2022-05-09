"""
Settings configuration file for local environment.
"""
import plaid

from happybudget.conf import Environments

from .base import *  # noqa

DEBUG = True
EMAIL_ENABLED = True
ENVIRONMENT = Environments.LOCAL

APP_DOMAIN = 'local.happybudget.io:8000'
APP_URL = 'http://%s' % APP_DOMAIN
FRONTEND_URL = "http://local.happybudget.io:3000"

DEFAULT_FILE_STORAGE = 'happybudget.app.io.storages.LocalStorage'

WAITLIST_ENABLED = False
EMAIL_VERIFICATION_ENABLED = False

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
JWT_COOKIE_SECURE = False

# When developing locally, the cookie names must differ from those used in
# production environments because these cookies are not being set in a secure
# context, and browsers will not let us override a cookie that was previously
# set in a secure context with the same cookie in an insecure context.
JWT_TOKEN_COOKIE_NAME = 'localhappybudgetjwt'
CSRF_COOKIE_NAME = 'localhappybudgetcsrftoken'
SESSION_COOKIE_NAME = 'localhappybudgetsessionid'

CSRF_TRUSTED_ORIGINS = [
    'http://local.happybudget.io:3000'
]
ALLOWED_HOSTS = [
    'local.happybudget.io'
]

# CORS Configuration
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_REGEX_WHITELIST = (
    r'^(https?://)?localhost:?[\d]*?$',
    r'^(https?://)?127.0.0.1:?[\d]*?$',
    r'^(https?://)?local.happybudget.io:?[\d]*?$'
)

# For an explanation as to why LocMemCache is used, see documentation in regard
# to :obj:`happybudget.app.cache.endpoint_cache`.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'
    }
}

CACHE_ENABLED = False

# Plaid Configurations
PLAID_ENVIRONMENT = plaid.Environment.Sandbox
