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
    'https://www.greenbudget.io',
]
