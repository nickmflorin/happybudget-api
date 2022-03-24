import copy
import logging
import sys


AWS_HANDLER = {
    "level": logging.INFO,
    "class": "watchtower.CloudWatchLogHandler",
    "log_group": "greenbudget-dev-api",
    "stream_name": "logstream",
    "formatter": "aws",
}

SENTRY_HANDLER = {
    'level': logging.WARNING,
    'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
}

# Loggers that will issue their logs to AWS Cloudwatch.
AWS_LOGGERS = ("django", "django.request", "django.server", "greenbudget")
# Loggers that will issue their logs with level greater than or equal to warning
# to Sentry.
SENTRY_LOGGERS = ("root", "greenbudget")


def attach_aws_logger(config, boto3_session):
    handler = copy.deepcopy(AWS_HANDLER)
    handler['boto3_session'] = boto3_session
    config["handlers"].update(watchtower=handler)
    for logger_name in AWS_LOGGERS:
        config["loggers"][logger_name]["handlers"] += ["watchtower"]


def attach_sentry_logger(config):
    config["handlers"].update(sentry=SENTRY_HANDLER)
    for logger_name in AWS_LOGGERS:
        config["loggers"][logger_name]["handlers"] += ["sentry"]


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': (
                '[%(name)s] %(levelname)s [%(module)s:L%(lineno)d; '
                '%(funcName)s()]: %(message)s'
            ),
        },
        'simple': {
            'format': '[%(name)s] %(levelname)s: %(message)s',
        },
        'dynamic': {
            '()': (
                'greenbudget.lib.logging.formatters.'
                'DynamicExtraArgumentFormatter'
            ),
        },
        'django.server': {
            '()': 'django.utils.log.ServerFormatter',
            'format': '[{server_time}] {message}',
            'style': '{',
        },
        "aws": {
            '()': (
                'greenbudget.lib.logging.formatters.'
                'DynamicExtraArgumentFormatter'
            ),
        },
    },
    'handlers': {
        'console': {
            'level': logging.DEBUG,
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'verbose'
        },
        'console.simple': {
            'level': logging.DEBUG,
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'simple'
        },
        'greenbudget.handler': {
            'level': logging.DEBUG,
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'dynamic'
        },
        'django.server': {
            'level': logging.INFO,
            'class': 'logging.StreamHandler',
            'formatter': 'django.server',
        },
        'django.request': {
            'level': logging.INFO,
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {'handlers': ['console'], 'level': logging.INFO},
    'loggers': {
        'root': {
            'level': logging.WARNING,
            'handlers': [],
        },
        'django': {
            'handlers': ['console.simple'],
            'level': logging.INFO,
            'propagate': True,
        },
        'django.server': {
            'handlers': ['django.server'],
            'level': logging.INFO,
            'propagate': False,
        },
        'django.request': {
            'handlers': ['django.request'],
            'level': logging.INFO,
            'propagate': False,
        },
        'requests': {'level': logging.WARNING},
        'greenbudget': {
            'handlers': ['greenbudget.handler'],
            'level': logging.INFO,
            'propagate': False,
        },
        '': {
            'level': logging.DEBUG,
            'handlers': ['console'],
            'propagate': False,
        },
    },
}
