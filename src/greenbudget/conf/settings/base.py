"""
Default settings configurations for all environments.

Each separate environment will import these configurations and override on a
per-case basis.
"""
import datetime
import os
from pathlib import Path

from greenbudget.conf import Environments, config

from .admin import *  # noqa
from .aws import *  # noqa
from .logging import *  # noqa

DEBUG = False

BASE_DIR = Path(os.path.abspath(__file__)).parents[2]
ROOT_DIR = Path(os.path.abspath(__file__)).parents[4]
APPS_DIR = BASE_DIR / "app"

# Localization Configuration
TIME_ZONE = 'UTC'
USE_TZ = True

APP_DOMAIN = 'api.greenbudget.cloud/'
APP_URL = 'https://%s' % APP_DOMAIN
APP_V1_URL = os.path.join(APP_URL, "v1")

SECRET_KEY = config(
    name='DJANGO_SECRET_KEY',
    required=[Environments.PROD, Environments.DEV],
    default={
        Environments.TEST: 'thefoxjumpedoverthelog',
        Environments.LOCAL: 'thefoxjumpedoverthelog'
    }
)

# Email Configurations
EMAIL_ENABLED = True
FROM_EMAIL = 'support@nirvedacognition.ai'
EMAIL_HOST = '.greenbudget.cloud'
SMTP_EMAIL_PORT = 25

PWD_RESET_LINK_EXPIRY_TIME_IN_HRS = 24
GOOGLE_OAUTH_API_URL = "https://www.googleapis.com/oauth2/v3/tokeninfo/"

# Session Configuration
SESSION_COOKIE_NAME = 'greenbudgetsessionid'
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_DOMAIN = ".greenbudget.cloud"
SESSION_COOKIE_AGE = 60 * 60 * 24
#: Extend the session on every request
SESSION_SAVE_EVERY_REQUEST = True

# CSRF Configuration
CSRF_COOKIE_SECURE = True
# Must be false so that the frontend can include as a header.
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_NAME = 'greenbudgetcsrftoken'
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_DOMAIN = ".greenbudget.cloud"
CSRF_TRUSTED_ORIGINS = [
    'https://app.greenbudget.cloud',
]
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_ALLOW_ALL = False
CORS_ORIGIN_REGEX_WHITELIST = (
    r'^(https?://)?([\w\.-]*?)\.greenbudget\.cloud:?[\d]*?$',
)

ALLOWED_HOSTS = [
    'api.greenbudget.cloud',
    '172.31.88.83',
    'gb-dev-lb-563148772.us-east-1.elb.amazonaws.com',  # Load Balancer
]

# JWT Configuration
JWT_COOKIE_SECURE = True
JWT_TOKEN_COOKIE_NAME = 'greenbudgetjwt'
JWT_COOKIE_DOMAIN = ".greenbudget.cloud"
SIMPLE_JWT = {
    'AUTH_TOKEN_CLASSES': (
        'greenbudget.app.jwt.tokens.GreenbudgetSlidingToken',),
    'SLIDING_TOKEN_LIFETIME': datetime.timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': datetime.timedelta(days=1),
    # We can use the SECRET_KEY temporarily, but it is not as secure as using
    # an RSA fingerprint in an ENV file.
    # 'SIGNING_KEY': SECRET_KEY,
    'SIGNING_KEY': config('SIMPLE_JWT_SIGNING_KEY', b'\n'.join([
        b'-----BEGIN RSA PRIVATE KEY-----',
        b'MIIBOwIBAAJBAJttTMyo2bRC5nJZ6tR8DqJiWa4NntaNfWCntw1nif0zFDFW0DcJ',
        b'PI1buHCf8XymwnkT35oW48v8JzPWQVYaM6cCAwEAAQJAHO0hnvFJ2x+cTenoJ3WT',
        b'L6uILzl/t0SL8gIkskzzxHiDkL9PNS8Ax0US+onurVj+wVRV7W278D98BvS7WTSa',
        b'OQIhANuk0Twne3G67nk5zVXFo9DsxTO4frJiFLBjXZ9rR+WjAiEAtSdbymlMI+SA',
        b'TK0TRSa92KtpJ2JTYlbA5uf2dCm/Mi0CIQC4AEzgbdr2HblliMzBi/5+KbvSZj6N',
        b'Rak7UyK9SGxErQIgI8HJFIMETHFmAbyH+TZUctgiwWtfGiIVoX5X30X+P2ECIQDG',
        b'+d6FMgY+Tne95/2/gV76/1MNJhjQaSpDUEJdRmpUpQ==',
        b'-----END RSA PRIVATE KEY-----',
    ]), cast=bytes),
    'VERIFYING_KEY': config('SIMPLE_JWT_VERIFYING_KEY', b'\n'.join([
        b'-----BEGIN PUBLIC KEY-----',
        b'MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBAJttTMyo2bRC5nJZ6tR8DqJiWa4NntaN',
        b'fWCntw1nif0zFDFW0DcJPI1buHCf8XymwnkT35oW48v8JzPWQVYaM6cCAwEAAQ==',
        b'-----END PUBLIC KEY-----',
    ]), cast=bytes),
    'ALGORITHM': 'RS256',
    'ROTATE_REFRESH_TOKENS': True,
    'USER_ID_FIELD': 'pk',
    'USER_ID_CLAIM': 'user_id',
}

AUTH_USER_MODEL = 'user.User'

TRACK_MODEL_HISTORY = True

INSTALLED_APPS = [
    'grappelli',
    'greenbudget',  # Must be before django authentication.
    'polymorphic',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'phonenumber_field',
    'colorful',
    'rest_framework',
    'generic_relations',
    'corsheaders',
    'timezone_field',
    'greenbudget.app.account',
    'greenbudget.app.actual',
    'greenbudget.app.authentication',
    'greenbudget.app.budget',
    'greenbudget.app.comment',
    'greenbudget.app.contact',
    'greenbudget.app.common',
    'greenbudget.app.fringe',
    'greenbudget.app.group',
    'greenbudget.app.history',
    'greenbudget.app.subaccount',
    'greenbudget.app.tagging',
    'greenbudget.app.template',
    'greenbudget.app.user',
    'greenbudget.app.jwt'
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'greenbudget.app.jwt.middleware.TokenCookieMiddleware',
    'greenbudget.lib.model_tracker.TrackModelMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = 'greenbudget.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'greenbudget.wsgi.application'

DATABASE_NAME = config(
    name='DATABASE_NAME',
    required=[Environments.PROD, Environments.DEV],
    default={
        Environments.TEST: 'postgres',
        Environments.LOCAL: 'postgres'
    }
)
DATABASE_USER = config(
    name='DATABASE_USER',
    required=[Environments.PROD, Environments.DEV],
    default={
        Environments.TEST: 'postgres',
        Environments.LOCAL: 'postgres'
    }
)
DATABASE_PASSWORD = config(
    name='DATABASE_PASSWORD',
    required=[Environments.PROD, Environments.DEV],
    default={
        Environments.TEST: '',
        Environments.LOCAL: ''
    }
)
DATABASE_HOST = config(
    name='DATABASE_HOST',
    required=[Environments.PROD, Environments.DEV],
    default={
        Environments.TEST: 'localhost',
        Environments.LOCAL: 'localhost'
    }
)
DATABASE_PORT = config(
    name='DATABASE_PORT',
    required=[Environments.PROD, Environments.DEV],
    default={
        Environments.TEST: '5432',
        Environments.LOCAL: '5432'
    }
)
DATABASES = {
    'default': {
        'ATOMIC_REQUESTS': True,
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': DATABASE_NAME,
        'USER': DATABASE_USER,
        'HOST': DATABASE_HOST,
        'PASSWORD': DATABASE_PASSWORD,
        'PORT': DATABASE_PORT
    },
}

STATIC_URL = '/static/'
STATIC_ROOT = str(BASE_DIR / "static")

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

REST_FRAMEWORK = {
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
    'NON_FIELD_ERRORS_KEY': '__all__',
    'EXCEPTION_HANDLER': (
        'greenbudget.lib.rest_framework_utils.views.exception_handler'),
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework_filters.backends.RestFrameworkFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication'
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'greenbudget.lib.rest_framework_utils.pagination.Pagination',  # noqa
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '20/minute',
        'user': '120/minute'
    }
}
