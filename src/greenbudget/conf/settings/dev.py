"""
Settings configuration file for development environment.
"""
from boto3 import session
import plaid

from greenbudget.conf import Environments

from .base import *  # noqa
from .base import (
    SENTRY_DSN, LOGGING, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY,
    AWS_DEFAULT_REGION, AWS_STORAGE_BUCKET_URL)
from .logging import attach_aws_logger, attach_sentry_logger


ENVIRONMENT = Environments.DEV
CACHE_ENABLED = False

APP_DOMAIN = 'devapi.greenbudget.io'  # Post Copyright Infringement
APP_URL = 'https://%s' % APP_DOMAIN
FRONTEND_URL = "https://dev.greenbudget.io/"  # Post Copyright Infringement

CSRF_TRUSTED_ORIGINS = [
    'https://dev.greenbudget.io',  # Post Copyright Infringement
    'https://devapi.greenbudget.io',  # Post Copyright Infringement
]

ALLOWED_HOSTS = ['devapi.greenbudget.io']  # Post Copyright Infringement

STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATIC_URL = AWS_STORAGE_BUCKET_URL

# Sentry is a configuration that is temporarily optional.  See note related
# to `Post Copyright Infringement`.
RAVEN_CONFIG = None
if SENTRY_DSN is not None:
    RAVEN_CONFIG = {
        "dsn": SENTRY_DSN,
        "environment": "development"
    }
    attach_sentry_logger(LOGGING)

attach_aws_logger(LOGGING, session.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION,
))

# Plaid Configurations
PLAID_ENVIRONMENT = plaid.Environment.Development
