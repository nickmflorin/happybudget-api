"""
Settings configuration file for production environment.
"""
from greenbudget.conf import Environments

from .base import *  # noqa

ENVIRONMENT = Environments.PROD

CORS_ORIGIN_ALLOW_ALL = False
CORS_ORIGIN_REGEX_WHITELIST = (
    r'^(https?://)?([\w\.-]*?)\.greenbudget\.io$',
    r'^(https?://)?master.d2er1ogdont4na.amplifyapp.com$',
)

ALLOWED_HOSTS = [
    '3.88.164.226',
]
