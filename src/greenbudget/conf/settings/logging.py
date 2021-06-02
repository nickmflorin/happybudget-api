import logging
import sys


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[%(name)s] %(levelname)s [%(module)s:L%(lineno)d; %(funcName)s()]: %(message)s',  # noqa
        },
        'simple': {
            'format': '[%(name)s] %(levelname)s: %(message)s',
        },
        'dynamic': {
            '()': 'greenbudget.lib.logging.formatters.DynamicExtraArgumentFormatter',  # noqa
        },
        'django.server': {
            '()': 'django.utils.log.ServerFormatter',
            'format': '[{server_time}] {message}',
            'style': '{',
        },
        "aws": {
            '()': 'greenbudget.lib.logging.formatters.DynamicExtraArgumentFormatter',  # noqa
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
