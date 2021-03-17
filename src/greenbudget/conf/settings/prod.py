"""
Settings configuration file for production environment.
"""
from greenbudget.conf import Environments

from .base import *  # noqa

ENVIRONMENT = Environments.PROD

CORS_ORIGIN_ALLOW_ALL = False
CORS_ORIGIN_REGEX_WHITELIST = (
    r'^(https?://)?([\w\.-]*?)\.greenbudget\.io$',
)

ALLOWED_HOSTS = [
    'https://3.88.164.226',
]

DATABASES = {
    'default': {
        'ATOMIC_REQUESTS': True,
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': "postgres",
        'USER': "postgres",
        'HOST': "0.0.0.0",
        'PORT': '5432'
    },
}
