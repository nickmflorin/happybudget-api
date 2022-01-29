"""
Settings configuration file for development environment.
"""
from boto3 import session
import logging

from greenbudget.conf import Environments, config

from .base import *  # noqa
from .base import (
    SENTRY_DSN, LOGGING, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY,
    AWS_DEFAULT_REGION)

ENVIRONMENT = Environments.DEV

APP_DOMAIN = 'devapi.greenbudget.io'
APP_URL = 'https://%s' % APP_DOMAIN
FRONTEND_URL = "https://dev.greenbudget.io/"

CSRF_TRUSTED_ORIGINS = [
    'https://dev.greenbudget.io',
    'https://devapi.greenbudget.io',
]

ALLOWED_HOSTS = [
    'devapi.greenbudget.io',
    'gb-dev-lb-563148772.us-east-1.elb.amazonaws.com',  # Load Balancer
]

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

LOGGING["handlers"]["watchtower"] = {
    "level": logging.INFO,
    "class": "watchtower.CloudWatchLogHandler",
    "log_group": "greenbudget-dev-api",
    "stream_name": "logstream",
    "formatter": "aws",
    "boto3_session": logger_boto3_session
}

for logger_name in ("django", "django.request", "django.server", "greenbudget"):
    LOGGING["loggers"][logger_name]["handlers"] = LOGGING[
        "loggers"][logger_name]["handlers"] + ["watchtower"]
