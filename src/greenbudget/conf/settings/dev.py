"""
Settings configuration file for development environment.
"""
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
import os

from greenbudget.conf import Environments

from .base import *  # noqa

ENVIRONMENT = Environments.DEV

APP_DOMAIN = '127.0.0.1:8000'
APP_URL = 'http://%s' % APP_DOMAIN
APP_V1_URL = os.path.join(APP_URL, "v1")
FRONTEND_URL = "https://dev.greenbudget.cloud/"

CSRF_TRUSTED_ORIGINS = [
    'https://dev.greenbudget.cloud',
]

ALLOWED_HOSTS = [
    'devapi.greenbudget.cloud',
    'gb-dev-lb-563148772.us-east-1.elb.amazonaws.com',  # Load Balancer
]

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

sentry_sdk.init(
    dsn="https://9eeab5e26f804bd582385ffc5eda991d@o591585.ingest.sentry.io/5740484",  # noqa
    integrations=[DjangoIntegration()],
    # Set traces_sample_rate to 1.0 to capture 100% of transactions for
    # performance monitoring. We recommend adjusting this value in production.
    traces_sample_rate=1.0,
    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    send_default_pii=True,
    environment="development"
)
