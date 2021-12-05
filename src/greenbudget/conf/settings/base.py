"""
Default settings configurations for all environments.

Each separate environment will import these configurations and override on a
per-case basis.
"""
import datetime
import os
from pathlib import Path

from greenbudget.conf import Environments, config, LazySetting

from .admin import *  # noqa
from .aws import *  # noqa
from .jwt_rsa_fingerprint import __JWT_SIGNING_KEY, __JWT_VERIFYING_KEY
from .logging import *  # noqa
from .password_validators import *  # noqa

DEBUG = False

BASE_DIR = Path(os.path.abspath(__file__)).parents[2]
ROOT_DIR = Path(os.path.abspath(__file__)).parents[4]
APPS_DIR = BASE_DIR / "app"

# Localization Configuration
TIME_ZONE = 'UTC'
USE_TZ = True

APP_DOMAIN = 'api.greenbudget.io/'
APP_URL = 'https://%s' % APP_DOMAIN

APP_V1_URL = LazySetting(
    lambda settings: os.path.join(str(settings.APP_URL), "v1"))

FRONTEND_URL = "https://app.greenbudget.io/"
FRONTEND_EMAIL_CONFIRM_URL = LazySetting(
    lambda settings: os.path.join(str(settings.FRONTEND_URL), "verify"))
FRONTEND_PASSWORD_RECOVERY_URL = LazySetting(
    lambda settings: os.path.join(str(settings.FRONTEND_URL), "recovery"))


SECRET_KEY = config(
    name='DJANGO_SECRET_KEY',
    required=[Environments.PROD, Environments.DEV],
    default={
        Environments.TEST: 'thefoxjumpedoverthelog',
        Environments.LOCAL: 'thefoxjumpedoverthelog'
    }
)

# Sentry Configuration
SENTRY_DSN = "https://9eeab5e26f804bd582385ffc5eda991d@o591585.ingest.sentry.io/5740484"  # noqa

# Email Configurations
EMAIL_ENABLED = True
FROM_EMAIL = "noreply@greenbudget.io"
EMAIL_HOST = 'smtp.sendgrid.net'
SENDGRID_API_KEY = config(
    name='SENDGRID_API_KEY',
    required=[Environments.PROD, Environments.DEV, Environments.LOCAL],
)
PASSWORD_RECOVERY_TEMPLATE_ID = "d-577a2dda8c2d4e3dabff2337240edf79"
EMAIL_VERIFICATION_TEMPLATE_ID = "d-3f3c585c80514e46809b9d3a46134674"

PWD_RESET_LINK_EXPIRY_TIME_IN_HRS = 24
GOOGLE_OAUTH_API_URL = "https://www.googleapis.com/oauth2/v3/tokeninfo/"

# Session Configuration
SESSION_COOKIE_NAME = 'greenbudgetsessionid'
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_DOMAIN = ".greenbudget.io"
SESSION_COOKIE_AGE = 60 * 60 * 24
#: Extend the session on every request
SESSION_SAVE_EVERY_REQUEST = True

# CSRF Configuration
CSRF_COOKIE_SECURE = True
# Must be false so that the frontend can include as a header.
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_NAME = 'greenbudgetcsrftoken'
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_DOMAIN = ".greenbudget.io"
CSRF_TRUSTED_ORIGINS = [
    'https://app.greenbudget.io',
]
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_ALLOW_ALL = False
CORS_ORIGIN_REGEX_WHITELIST = (
    r'^(https?://)?([\w\.-]*?)\.greenbudget\.io:?[\d]*?$',
)

ALLOWED_HOSTS = [
    'api.greenbudget.io',
    '172.31.88.83',
    'gb-lb-1485149386.us-east-2.elb.amazonaws.com',  # Load Balancer
]

# We store these externally because rest_framework_simplejwt's reload settings
# does not work properly, which means that when we override these values in
# tests they do not properly update on the tokens.  Instead, we manually set
# these values inside the tokens __init__ methods so they reflect any changes
# to settings that may occur.
ACCESS_TOKEN_LIFETIME = datetime.timedelta(minutes=15)
SLIDING_TOKEN_REFRESH_LIFETIME = datetime.timedelta(days=3)
SLIDING_TOKEN_LIFETIME = datetime.timedelta(minutes=5)

# JWT Configuration
JWT_COOKIE_SECURE = True
JWT_TOKEN_COOKIE_NAME = 'greenbudgetjwt'
JWT_COOKIE_DOMAIN = ".greenbudget.io"


SIMPLE_JWT = {
    'AUTH_TOKEN_CLASSES': ('greenbudget.app.authentication.tokens.AuthToken',),
    'SLIDING_TOKEN_LIFETIME': SLIDING_TOKEN_LIFETIME,
    'ACCESS_TOKEN_LIFETIME': ACCESS_TOKEN_LIFETIME,
    'SLIDING_TOKEN_REFRESH_LIFETIME': SLIDING_TOKEN_REFRESH_LIFETIME,
    # 'SIGNING_KEY': SECRET_KEY,
    # We can use the SECRET_KEY temporarily when developing locally, but it
    # is not nearly as secure as using an RSA fingerprint in the ENV file.
    'SIGNING_KEY': __JWT_SIGNING_KEY,
    'VERIFYING_KEY': __JWT_VERIFYING_KEY,
    'ALGORITHM': 'RS256',
    'ROTATE_REFRESH_TOKENS': True,
    'USER_ID_FIELD': 'pk',
    'USER_ID_CLAIM': 'user_id',
}

AUTH_USER_MODEL = 'user.User'

INSTALLED_APPS = [
    'compressor',
    'grappelli.dashboard',
    'grappelli',
    'greenbudget',  # Must be before django authentication.
    'polymorphic',
    'raven.contrib.django.raven_compat',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'colorful',
    'rest_framework',
    'generic_relations',
    'corsheaders',
    'timezone_field',
    'greenbudget.app',
    'greenbudget.app.account',
    'greenbudget.app.actual',
    'greenbudget.app.authentication',
    'greenbudget.app.budget',
    'greenbudget.app.budgeting',
    'greenbudget.app.contact',
    'greenbudget.app.custom_admin',
    'greenbudget.app.fringe',
    'greenbudget.app.group',
    'greenbudget.app.io',
    'greenbudget.app.markup',
    'greenbudget.app.pdf',
    'greenbudget.app.subaccount',
    'greenbudget.app.tabling',
    'greenbudget.app.tagging',
    'greenbudget.app.template',
    'greenbudget.app.user',
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'greenbudget.app.middleware.HealthCheckMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'greenbudget.app.authentication.middleware.TokenCookieMiddleware',
    'greenbudget.app.signals.middleware.ModelSignalMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = 'greenbudget.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        # 'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader'
            ]
        },
    },
]

WSGI_APPLICATION = 'greenbudget.wsgi.application'

# NOTE: If Django is not starting because the database does not exist, we need
# to create one with postgres.  Go into the Postgres shell (psql) and do
# the following:
# >>> CREATE USER greenbudget WITH PASSWORD '';
# >>> CREATE DATABASE postgres_greenbudget WITH OWNER greenbudget ENCODING
#     utf-8';
DATABASE_NAME = config(
    name='DATABASE_NAME',
    required=[Environments.PROD, Environments.DEV],
    default={
        Environments.TEST: 'postgres_greenbudget',
        Environments.LOCAL: 'postgres_greenbudget'
    }
)
DATABASE_USER = config(
    name='DATABASE_USER',
    required=[Environments.PROD, Environments.DEV],
    default={
        Environments.TEST: 'greenbudget',
        Environments.LOCAL: 'greenbudget'
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

ELASTICACHE_ENDPOINT = config(
    name='ELASTICACHE_ENDPOINT',
    required=[Environments.PROD, Environments.DEV],
    default={
        Environments.TEST: '',
        Environments.LOCAL: ''
    }
)

CACHE_ENABLED = False
CACHE_LOCATION = f"redis://{ELASTICACHE_ENDPOINT}/0"
CACHE_EXPIRY = 5 * 60 * 60

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': CACHE_LOCATION,
        'OPTIONS': {
            'REDIS_CLIENT_CLASS': 'rediscluster.RedisCluster',
            'CONNECTION_POOL_CLASS': (
                'rediscluster.connection.ClusterConnectionPool'),
            'CONNECTION_POOL_KWARGS': {
                # AWS ElastiCache has configuration commands disabled.
                'skip_full_coverage_check': True
            }
        }
    }
}

FIXTURES = [
    'colors.json',
    'tags.json',
    'subaccountunits.json',
    'actualtypes.json'
]

ACCEPTED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png']
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

STATIC_URL = '/static/'
STATIC_ROOT = str(BASE_DIR / "static")
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

# Only applicable for image uploads locally.
MEDIA_URL = '/media/'
MEDIA_ROOT = str(BASE_DIR / "media")

COMPRESS_PRECOMPILERS = (
    ('text/x-scss', 'django_libsass.SassCompiler'),
)

AUTHENTICATION_BACKENDS = (
    'greenbudget.app.authentication.backends.ModelAuthentication',
    'greenbudget.app.authentication.backends.SocialModelAuthentication',
)

REST_FRAMEWORK = {
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
    'NON_FIELD_ERRORS_KEY': '__all__',
    'EXCEPTION_HANDLER': 'greenbudget.app.views.exception_handler',
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'greenbudget.app.authentication.backends.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'greenbudget.app.authentication.permissions.IsAuthenticated',
        'greenbudget.app.authentication.permissions.IsVerified'
    ],
    'DEFAULT_PAGINATION_CLASS': 'greenbudget.lib.drf.pagination.Pagination',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '20/minute',
        'user': '120/minute'
    }
}
