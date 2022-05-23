"""
Default settings configurations for all environments.

Each separate environment will import these configurations and override on a
per-case basis.

Post Copyright Infringement:
---------------------------
Any configuration marked with 'Post Copyright Infringement' denotes that the
relevant configuration was related to entities that were under the ownership
of Saturation IO, who has since stolen this software in a manner that infringes
upon its copyright.  As such, the relevant configuration is turned off until
it can be reconfigured under new ownership.
"""
import datetime
import os

from corsheaders.defaults import default_headers
import plaid

from happybudget.conf import Environments, config, LazySetting

from .admin import *  # noqa
from .aws import *  # noqa
from .cache import *  # noqa
from .celery import *  # noqa
from .constant import *  # noqa
from .constant import BASE_DIR
from .db import *  # noqa
from .jwt_rsa_fingerprint import __JWT_SIGNING_KEY, __JWT_VERIFYING_KEY
from .logging import *  # noqa
from .password_validators import *  # noqa
from .email import *  # noqa
from .stripe import *  # noqa

DEBUG = False

# Localization Configuration
TIME_ZONE = 'UTC'
USE_TZ = True

APP_DOMAIN = 'api.happybudget.io/'  # Post Copyright Infringement
APP_URL = 'https://%s' % APP_DOMAIN

APP_V1_URL = LazySetting(
    lambda settings: os.path.join(str(settings.APP_URL), "v1"))

FRONTEND_URL = "https://app.happybudget.io/"  # Post Copyright Infringement

SECRET_KEY = config(
    name='DJANGO_SECRET_KEY',
    required=[Environments.PROD, Environments.DEV],
    default={
        Environments.TEST: 'thefoxjumpedoverthelog',
        Environments.LOCAL: 'thefoxjumpedoverthelog'
    }
)

# Sentry Configuration - Post Copyright Infringement
SENTRY_DSN = None

PWD_RESET_LINK_EXPIRY_TIME_IN_HRS = 24

SOCIAL_AUTHENTICATION_ENABLED = False
GOOGLE_OAUTH_API_URL = None  # Post Copyright Infringement

# Public Configuration
PUBLIC_TOKEN_HEADER = "HTTP_X_PUBLICTOKEN"

# Session Configuration
SESSION_COOKIE_NAME = 'happybudgetsessionid'
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_DOMAIN = ".happybudget.io"
SESSION_COOKIE_AGE = 60 * 60 * 24
SESSION_SAVE_EVERY_REQUEST = True

# CSRF Configuration
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False  # So frontend can include as a header.
CSRF_COOKIE_NAME = 'happybudgetcsrftoken'
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_DOMAIN = ".happybudget.io"
CSRF_TRUSTED_ORIGINS = [
    'https://app.happybudget.io',
    'https://api.happybudget.io',
]

# CORS Configuration
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_ALLOW_ALL = False
CORS_ORIGIN_REGEX_WHITELIST = (
    r'^(https?://)?([\w\.-]*?)\.happybudget\.io:?[\d]*?$',
)
CORS_ALLOW_HEADERS = list(default_headers) + [
    "x-publictoken",
]

ALLOWED_HOSTS = ['api.happybudget.io']

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
JWT_TOKEN_COOKIE_NAME = 'happybudgetjwt'
JWT_COOKIE_DOMAIN = ".happybudget.io"

SIMPLE_JWT = {
    'AUTH_TOKEN_CLASSES': ('happybudget.app.authentication.tokens.AuthToken',),
    'SLIDING_TOKEN_LIFETIME': SLIDING_TOKEN_LIFETIME,
    'ACCESS_TOKEN_LIFETIME': ACCESS_TOKEN_LIFETIME,
    'SLIDING_TOKEN_REFRESH_LIFETIME': SLIDING_TOKEN_REFRESH_LIFETIME,
    # We can use the SECRET_KEY temporarily when developing locally, but it
    # is not nearly as secure as using an RSA fingerprint in the ENV file.
    # 'SIGNING_KEY': SECRET_KEY,
    'SIGNING_KEY': __JWT_SIGNING_KEY,
    'VERIFYING_KEY': __JWT_VERIFYING_KEY,
    'ALGORITHM': 'RS256',
    'ROTATE_REFRESH_TOKENS': True,
    'USER_ID_FIELD': 'pk',
    'USER_ID_CLAIM': 'user_id',
}

AUTH_USER_MODEL = 'user.User'

# When True, a staff user will be granted global permissions for all endpoints.
# This means that they will be able to access information related to any user.
# This flag is used for production environments, where we may need to diagnose
# problems that a real user is having inside the application.
STAFF_USER_GLOBAL_PERMISSIONS = False

# When True, User's will not be allowed to register unless they are on a
# waitlist in SendGrid.
WAITLIST_ENABLED = False  # Post Copyright Infringement
EMAIL_VERIFICATION_ENABLED = False  # Post Copyright Infringement

INSTALLED_APPS = [
    'compressor',
    'grappelli.dashboard',
    'grappelli',
    'happybudget',  # Must be before django authentication.
    'polymorphic',
    'raven.contrib.django.raven_compat',
    'happybudget.harry.apps.HarryAdminConfig',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'colorful',
    'fontawesomefree',
    'rest_framework',
    'generic_relations',
    'nested_admin',
    'corsheaders',
    'timezone_field',
    'happybudget.app',
    'happybudget.data',
    'happybudget.app.account',
    'happybudget.app.actual',
    'happybudget.app.authentication',
    'happybudget.app.budget',
    'happybudget.app.budgeting',
    'happybudget.app.collaborator',
    'happybudget.app.contact',
    'happybudget.app.fringe',
    'happybudget.app.group',
    'happybudget.app.integrations',
    'happybudget.app.integrations.plaid',
    'happybudget.app.io',
    'happybudget.app.markup',
    'happybudget.app.pdf',
    'happybudget.app.subaccount',
    'happybudget.app.tabling',
    'happybudget.app.tagging',
    'happybudget.app.template',
    'happybudget.app.user'
]


MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'happybudget.app.middleware.HealthCheckMiddleware',
    'django.middleware.security.SecurityMiddleware',
    # This middleware must come before authentication middleware classes.
    'django.contrib.sessions.middleware.SessionMiddleware',
    'happybudget.app.authentication.middleware.PublicTokenMiddleware',
    # This middleware must come before the TokenCookieMiddleware.
    'happybudget.app.authentication.middleware.BillingTokenCookieMiddleware',
    'happybudget.app.authentication.middleware.AuthTokenCookieMiddleware',
    'happybudget.app.middleware.ModelRequestMiddleware',
    'happybudget.app.middleware.CacheUserMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = 'happybudget.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "harry" / "templates"],
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

WSGI_APPLICATION = 'happybudget.wsgi.application'

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

COMPRESS_ROOT = str(BASE_DIR / "harry" / "static")
COMPRESS_PRECOMPILERS = (
    ('text/x-scss', 'django_libsass.SassCompiler'),
)

AUTHENTICATION_BACKENDS = (
    'happybudget.app.authentication.backends.ModelAuthentication',
    'happybudget.app.authentication.backends.SocialModelAuthentication',
)

AUTHENTICATION_PERMISSION_CLASSES = [
    'happybudget.app.permissions.IsAuthenticated',
    'happybudget.app.permissions.IsActive',
    'happybudget.app.permissions.IsVerified'
]

REST_FRAMEWORK = {
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
    'NON_FIELD_ERRORS_KEY': '__all__',
    'EXCEPTION_HANDLER': 'happybudget.app.views.exception_handler',
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PERMISSION_CLASSES': AUTHENTICATION_PERMISSION_CLASSES,
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'happybudget.app.authentication.backends.SessionAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'happybudget.lib.drf.pagination.Pagination',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '20/minute',
        'user': '120/minute'
    }
}

# Plaid Configurations - Post Copyright Infringement All Configurations
PLAID_ENABLED = False
PLAID_ENVIRONMENT = plaid.Environment.Production
PLAID_CLIENT_NAME = 'HappyBudget\'s Finance App'

PLAID_CLIENT_ID = config(
    name='PLAID_CLIENT_ID',
    required=[Environments.PROD, Environments.DEV, Environments.LOCAL],
    default={Environments.TEST: ''},
    enabled=PLAID_ENABLED  # Post Copyright Infringement
)
PLAID_CLIENT_SECRET = config(
    name='PLAID_CLIENT_SECRET',
    required=[Environments.PROD, Environments.DEV, Environments.LOCAL],
    default={Environments.TEST: ''},
    enabled=PLAID_ENABLED  # Post Copyright Infringement
)
