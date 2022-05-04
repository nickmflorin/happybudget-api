"""
Default settings configurations for all environments.

Each separate environment will import these configurations and override on a
per-case basis.
"""
import datetime
import os

from corsheaders.defaults import default_headers
import plaid

from greenbudget.conf import Environments, config, LazySetting

from .admin import *  # noqa
from .aws import *  # noqa
from .cache import *  # noqa
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

APP_DOMAIN = 'api.greenbudget.io/'
APP_URL = 'https://%s' % APP_DOMAIN

APP_V1_URL = LazySetting(
    lambda settings: os.path.join(str(settings.APP_URL), "v1"))

FRONTEND_URL = "https://app.greenbudget.io/"

SECRET_KEY = config(
    name='DJANGO_SECRET_KEY',
    required=[Environments.PROD, Environments.DEV],
    default={
        Environments.TEST: 'thefoxjumpedoverthelog',
        Environments.LOCAL: 'thefoxjumpedoverthelog'
    }
)

# Sentry Configuration
# This configuration was related to entities that were under the ownership of
# Saturation IO - which has since stolen this software in a manner that
# infringes on its copyright.  As such, it will be turned off until the related
# entity can be reconfigured under new ownership.
SENTRY_DSN = "https://9eeab5e26f804bd582385ffc5eda991d@o591585.ingest.sentry.io/5740484"  # noqa

PWD_RESET_LINK_EXPIRY_TIME_IN_HRS = 24
GOOGLE_OAUTH_API_URL = "https://www.googleapis.com/oauth2/v3/tokeninfo/"

# Public Configuration
PUBLIC_TOKEN_HEADER = "HTTP_X_PUBLICTOKEN"

# Session Configuration
SESSION_COOKIE_NAME = 'greenbudgetsessionid'
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_DOMAIN = ".greenbudget.io"
SESSION_COOKIE_AGE = 60 * 60 * 24
SESSION_SAVE_EVERY_REQUEST = True

# CSRF Configuration
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False  # So frontend can include as a header.
CSRF_COOKIE_NAME = 'greenbudgetcsrftoken'
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_DOMAIN = ".greenbudget.io"
CSRF_TRUSTED_ORIGINS = [
    'https://app.greenbudget.io',
    'https://api.greenbudget.io',
]

# CORS Configuration
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_ALLOW_ALL = False
CORS_ORIGIN_REGEX_WHITELIST = (
    r'^(https?://)?([\w\.-]*?)\.greenbudget\.io:?[\d]*?$',
)
CORS_ALLOW_HEADERS = list(default_headers) + [
    "x-publictoken",
]

ALLOWED_HOSTS = ['api.greenbudget.io']

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

# When True, a staff user will be granted global permissions for all endpoints.
# This means that they will be able to access information related to any user.
# This flag is used for production environments, where we may need to diagnose
# problems that a real user is having inside the application.
STAFF_USER_GLOBAL_PERMISSIONS = False

# When True, User's will not be allowed to register unless they are on a
# waitlist in SendGrid.
WAITLIST_ENABLED = True
EMAIL_VERIFICATION_ENABLED = True

INSTALLED_APPS = [
    'compressor',
    'grappelli.dashboard',
    'grappelli',
    'greenbudget',  # Must be before django authentication.
    'polymorphic',
    'raven.contrib.django.raven_compat',
    'greenbudget.harry.apps.HarryAdminConfig',
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
    'greenbudget.app',
    'greenbudget.data',
    'greenbudget.app.account',
    'greenbudget.app.actual',
    'greenbudget.app.authentication',
    'greenbudget.app.budget',
    'greenbudget.app.budgeting',
    'greenbudget.app.collaborator',
    'greenbudget.app.contact',
    'greenbudget.app.fringe',
    'greenbudget.app.group',
    'greenbudget.app.integrations',
    'greenbudget.app.integrations.plaid',
    'greenbudget.app.io',
    'greenbudget.app.markup',
    'greenbudget.app.pdf',
    'greenbudget.app.subaccount',
    'greenbudget.app.tabling',
    'greenbudget.app.tagging',
    'greenbudget.app.template',
    'greenbudget.app.user'
]


MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'greenbudget.app.middleware.HealthCheckMiddleware',
    'django.middleware.security.SecurityMiddleware',
    # This middleware must come before authentication middleware classes.
    'django.contrib.sessions.middleware.SessionMiddleware',
    'greenbudget.app.authentication.middleware.PublicTokenMiddleware',
    # This middleware must come before the TokenCookieMiddleware.
    'greenbudget.app.authentication.middleware.BillingTokenCookieMiddleware',
    'greenbudget.app.authentication.middleware.AuthTokenCookieMiddleware',
    'greenbudget.app.middleware.ModelRequestMiddleware',
    'greenbudget.app.middleware.CacheUserMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = 'greenbudget.urls'

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

WSGI_APPLICATION = 'greenbudget.wsgi.application'

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
    'greenbudget.app.authentication.backends.ModelAuthentication',
    'greenbudget.app.authentication.backends.SocialModelAuthentication',
)

AUTHENTICATION_PERMISSION_CLASSES = [
    'greenbudget.app.permissions.IsAuthenticated',
    'greenbudget.app.permissions.IsActive',
    'greenbudget.app.permissions.IsVerified'
]

REST_FRAMEWORK = {
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
    'NON_FIELD_ERRORS_KEY': '__all__',
    'EXCEPTION_HANDLER': 'greenbudget.app.views.exception_handler',
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PERMISSION_CLASSES': AUTHENTICATION_PERMISSION_CLASSES,
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'greenbudget.app.authentication.backends.SessionAuthentication',
    ),
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

# Plaid Configurations
PLAID_ENVIRONMENT = plaid.Environment.Production
PLAID_CLIENT_NAME = 'GreenBudget\'s Finance App'

PLAID_CLIENT_ID = config(
    name='PLAID_CLIENT_ID',
    required=[Environments.PROD, Environments.DEV, Environments.LOCAL],
    default={Environments.TEST: ''}
)
PLAID_CLIENT_SECRET = config(
    name='PLAID_CLIENT_SECRET',
    required=[Environments.PROD, Environments.DEV, Environments.LOCAL],
    default={Environments.TEST: ''}
)
