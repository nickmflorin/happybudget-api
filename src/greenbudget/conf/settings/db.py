from greenbudget.conf import config, Environments

DEFAULT_BULK_BATCH_SIZE = 20

FIXTURES = [
    'colors.json',
    'tags.json',
    'subaccountunits.json',
    'actualtypes.json'
]

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
