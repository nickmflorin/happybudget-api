"""
Settings configuration file for development environment.
"""
from boto3 import session

from greenbudget.conf import Environments, config

from .base import *  # noqa
from .base import (
    SENTRY_DSN, LOGGING, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY,
    AWS_DEFAULT_REGION)
from .logging import attach_aws_logger, attach_sentry_logger


ENVIRONMENT = Environments.DEV
CACHE_ENABLED = False

APP_DOMAIN = 'devapi.greenbudget.io'
APP_URL = 'https://%s' % APP_DOMAIN
FRONTEND_URL = "https://dev.greenbudget.io/"

CSRF_TRUSTED_ORIGINS = [
    'https://dev.greenbudget.io',
    'https://devapi.greenbudget.io',
]

ALLOWED_HOSTS = ['devapi.greenbudget.io']

STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATIC_URL = config(
    name='AWS_STORAGE_BUCKET_URL',
    required=True,
    validate=lambda value: (value.endswith(
        '/'), "The URL must end with a trailing slash.")
)

RAVEN_CONFIG = {
    "dsn": SENTRY_DSN,
    "environment": "development"
}

logger_boto3_session = session.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION,
)

attach_aws_logger(LOGGING, logger_boto3_session)
attach_sentry_logger(LOGGING)
