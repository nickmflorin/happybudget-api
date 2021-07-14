"""
Settings configuration file for development environment.
"""
from boto3 import session
import logging
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
import os

from greenbudget.conf import Environments, config
from greenbudget.conf.util import get_ec2_hostname

from .base import *  # noqa
from .base import (
    LOGGING, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION)

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

print("Adding EC2 IP Address to Allowed Hosts")
ec2_host_name = get_ec2_hostname()
if ec2_host_name is not None:
    ALLOWED_HOSTS.append(ec2_host_name)

# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_STORAGE = True

STATIC_URL = config(
    name='AWS_STORAGE_BUCKET_URL',
    required=True
)

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
