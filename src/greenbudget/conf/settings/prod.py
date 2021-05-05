"""
Settings configuration file for production environment.
"""
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from greenbudget.conf import Environments

from .base import *  # noqa

ENVIRONMENT = Environments.PROD

sentry_sdk.init(
    dsn="https://9eeab5e26f804bd582385ffc5eda991d@o591585.ingest.sentry.io/5740484",  # noqa
    integrations=[DjangoIntegration()],
    # Set traces_sample_rate to 1.0 to capture 100% of transactions for
    # performance monitoring. We recommend adjusting this value in production.
    traces_sample_rate=1.0,
    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    send_default_pii=True,
    environment="production"
)
