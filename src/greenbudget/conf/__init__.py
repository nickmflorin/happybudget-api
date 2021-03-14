import os
import csv
from dotenv import load_dotenv
import logging
import pathlib
import sys


logger = logging.getLogger('greenbudget')


class Environments:
    PROD = "Production"
    DEV = "Development"
    TEST = "Test"


def get_environment():
    mapping = {
        'greenbudget.conf.settings.dev': Environments.DEV,
        'greenbudget.conf.settings.local': Environments.DEV,
        'greenbudget.conf.settings.gunicorn_dev': Environments.DEV,
        'greenbudget.conf.settings.prod': Environments.PROD,
        'greenbudget.conf.settings.test': Environments.TEST
    }
    django_settings_module = os.getenv(
        'DJANGO_SETTINGS_MODULE', 'greenbudget.conf.settings.prod')
    return mapping[django_settings_module]


class ConfigError(Exception):
    pass


class ConfigInvalidError(ConfigError):

    def __init__(self, config_name):
        self.config_name = config_name

    def __str__(self):
        return f"The {self.config_name} environment variable is invalid."


class ConfigRequiredError(ConfigError):

    def __init__(self, config_name):
        self.config_name = config_name

    def __str__(self):
        return f"{self.config_name} is a required environment variable."


class Config:
    """
    Loads configuration settings from shell environment or .env file, the name
    for which can be overriden by exporting DOTENV_PATH in your shell.
    """

    def __init__(self, filepath=None, filename=None):
        self._values = {}
        self._defaults = {}
        self._environment = get_environment()

        # Load environment variables from a .env file if it exists.
        dotenv_path = filepath or os.getenv('DOTENV_PATH', None)
        if dotenv_path is None:
            ROOT_DIR = pathlib.Path(os.path.abspath(__file__)).parents[3]
            dotenv_file = filename or os.getenv('DOTENV_FILE', ".env")
            dotenv_path = ROOT_DIR / dotenv_file

        # If the ENV file does not exist, we do not want an exception to be
        # raised.  This will cause issues with tests.  Instead, we just don't
        # load those values into the environment.
        if os.path.exists(dotenv_path):
            load_dotenv(dotenv_path=dotenv_path)
        else:
            # This is a temporary hack to allow the .env file inside the docker
            # container to be found correctly.
            load_dotenv(dotenv_path=".env")
            # if os.path.exists(".env"):
            #     load_dotenv(dotenv_path=".env")
            # else:
            #     logger.warning(
            #         "Could not find an ENV file at %s - not loading."
            #         % dotenv_path)

    def __call__(self, name, default='', cast=str, required=False):
        # Whether or not the configuration is required can be a function of
        # the environment we are in.
        if isinstance(required, dict):
            required = required.get(self._environment, False)
        elif (not isinstance(required, str)
                and hasattr(required, '__iter__')):
            required = self._environment in required

        # The configuration default can be a function of what environment we
        # are in.
        if isinstance(default, dict):
            default = default.get(self._environment, '')

        name = name.upper()
        if name not in self._values:
            value = os.getenv(name, default)
            if value is None:
                self._values[name] = self._defaults[name] = default
            else:
                try:
                    self._values[name] = cast(value)
                except ValueError:
                    raise ConfigInvalidError(name)

            if required and not self._values[name]:
                raise ConfigRequiredError(name)

        return self._values[name]

    @staticmethod
    def csvlist(value):
        if r'\n' in value:
            value = value.replace(r'\n', '\n')
        data = list(csv.reader(value.splitlines()))
        return data if len(data) > 1 else data[0]

    @staticmethod
    def bool(value):
        return value.upper() in ['YES', 'TRUE', '1']

    def write(self, filename=None):
        """
        Dumps all previously registered configuration values to either STDOUT
        or a provided filename.
        """
        lines = []
        for key, value in sorted(self._defaults.items()):
            lines.append('{}={}'.format(
                key,
                '' if value in (None, '') else value
            ))
        text = '\n'.join(lines)
        if filename:
            with open(filename) as fobj:
                fobj.write(text)
        else:
            sys.stdout.write(text)


config = Config()
