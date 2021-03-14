"""
Settings configuration file for dev environment when running gunicorn web
server.
"""
import os

from .dev import *  # noqa

APP_DOMAIN = '0.0.0.0:3000'
APP_URL = 'http://%s' % APP_DOMAIN
APP_V1_URL = os.path.join(APP_URL, "v1")

CSRF_COOKIE_DOMAIN = "0.0.0.0"
JWT_COOKIE_DOMAIN = '0.0.0.0'
SESSION_COOKIE_DOMAIN = '0.0.0.0'

CSRF_TRUSTED_ORIGINS = [
    '0.0.0.0',
]
ALLOWED_HOSTS = [
    '0.0.0.0',
]

DATABASES = {
    'default': {
        'ATOMIC_REQUESTS': True,
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': "postgres",
        'USER': "postgres",
        'HOST': "localhost",
        'PORT': '5432'
    },
}
