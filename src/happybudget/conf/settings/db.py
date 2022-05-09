import collections
import dj_database_url

from happybudget.conf import config, Environments
from .constant import ROOT_DIR


DbConfig = collections.namedtuple('Db', ['id', 'engine'])


class DatabaseEngine:
    POSTGRES = 'django.db.backends.postgresql'
    SQLITE = 'django.db.backends.sqlite3'


class DatabaseConfig:
    POSTGRES = DbConfig(id="postgres", engine=DatabaseEngine.POSTGRES)
    SQLITE = DbConfig(id="sqlite", engine=DatabaseEngine.SQLITE)
    __all__ = [POSTGRES, SQLITE]

    @classmethod
    def get(cls, config_id):
        if config_id not in [c.id for c in cls.__all__]:
            raise LookupError(f"Unknown database config id {config_id}.")
        return [c for c in cls.__all__ if c.id == config_id][0]


def db(config_id, *args, **kwargs):
    cfg = DatabaseConfig.get(config_id)
    default_data = {
        'ATOMIC_REQUESTS': ATOMIC_REQUESTS,
        'ENGINE': cfg.engine,
        'CONN_MAX_AGE': CONN_MAX_AGE
    }
    default_data.update(dict(*args, **kwargs))
    return default_data


def postgres_db(*args, **kwargs):
    return db('postgres', *args, **kwargs)


def sqlite_db(filename):
    return db(
        'sqlite',
        dj_database_url.parse(f'sqlite:///{ROOT_DIR}/{filename}')
    )


DEFAULT_BULK_BATCH_SIZE = 20
ATOMIC_REQUESTS = True
CONN_MAX_AGE = 500

FIXTURES = [
    'colors.json',
    'tags.json',
    'subaccountunits.json',
    'actualtypes.json'
]

"""
If Django is not starting because the database does not exist or we are getting
an error related to the role `happybudget` not existing, we need to do the
following (note that not all steps are required each time):

(1) Connect to Default Postgres Database:
    ------------------------------------
    Since we do not know whether or not the database we are concerned with has
    been created yet, we connect to the default database `postgres` since we
    can still run commands for other databases from that entry point.

    >>> psql -d postgres

(2) Create the Database
    -------------------
    If the database was not already created, we need to create it.

    >>> CREATE DATABASE <DATABASE_NAME>;

(3) Create the User
    ---------------
    If the user does not already exist, we need to create one in Postgres. Note
    that if different databases are using the same user, the user may already
    have been created.

    >>> CREATE USER <DATABASE_USER> WITH PASSWORD '';

(4) Grant Privileges to User
    ------------------------
    If the database was just created, or the user was just created, we need to
    grant access to the created or existing database to the created or existing
    user.

    >>> GRANT ALL PRIVILEGES ON DATABASE <DATABASE_NAME> TO <DATABASE_USER>;

(5) Set the Database Owner to User
    ------------------------------
    If the database was just created, or the user was just created, we need to
    assign the created or existing user as the owner of the created or existing
    database.

    >>> ALTER DATABASE <DATABASE_NAME> OWNER TO <DATABASE_USER>;

(6) Quit the Postgres Shell
    -----------------------
    >>> (backslash)q
"""
DATABASE_NAME = config(
    name='DATABASE_NAME',
    required=[Environments.PROD, Environments.DEV],
    default={
        Environments.TEST: 'postgres_happybudget',
        Environments.LOCAL: 'postgres_happybudget'
    }
)
DATABASE_USER = config(
    name='DATABASE_USER',
    required=[Environments.PROD, Environments.DEV],
    default={
        Environments.TEST: 'happybudget',
        Environments.LOCAL: 'happybudget'
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

LIVE_POSTGRES_DB = postgres_db(
    NAME=DATABASE_NAME,
    USER=DATABASE_USER,
    HOST=DATABASE_HOST,
    PASSWORD=DATABASE_PASSWORD,
    PORT=DATABASE_PORT
)

DATABASES = {
    'default': LIVE_POSTGRES_DB
}
