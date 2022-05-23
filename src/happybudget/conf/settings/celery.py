from happybudget.conf import config, Environments
from .aws import AWS_DEFAULT_REGION

CELERY_ENABLED = True

CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = "UTC"

CELERY_BROKER_URL = config(
    name='CELERY_BROKER_URL',
    required=[Environments.PROD, Environments.DEV],
    default={Environments.LOCAL: "redis://localhost:6379/0"}
)
CELERY_RESULT_BACKEND = CELERY_BROKER_URL

CELERY_BROKER_TRANSPORT_OPTIONS = {
    'region': AWS_DEFAULT_REGION,
    'polling_interval': 1,
    'visibility_timeout': 30,
    'is_secure': True,
}
