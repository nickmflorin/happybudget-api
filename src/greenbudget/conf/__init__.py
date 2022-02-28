import collections
import copy
import csv
from dotenv import load_dotenv
import functools
import logging
import os
import pathlib
import sys

from django.utils.functional import SimpleLazyObject

from greenbudget.lib.utils import humanize_list


logger = logging.getLogger('greenbudget')


def get_lazy_setting(func):
    from django.conf import settings
    return func(settings)


def LazySetting(func):
    return SimpleLazyObject(lambda: get_lazy_setting(func))


def suppress_with_setting(attr, value=False, suppressed_return_value=None):
    def decorator(func):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            from django.conf import settings
            current_value = getattr(settings, attr)
            if current_value != value:
                return func(*args, **kwargs)
            logger.warning("Skipping call to %s because %s = %s." % (
                func.__name__,
                attr,
                current_value
            ))
            return suppressed_return_value
        return inner
    return decorator


class Environments:
    PROD = "Production"
    DEV = "Development"
    TEST = "Test"
    LOCAL = "Local"


def get_environment():
    mapping = {
        'greenbudget.conf.settings.dev': Environments.DEV,
        'greenbudget.conf.settings.local': Environments.LOCAL,
        'greenbudget.conf.settings.prod': Environments.PROD,
        'greenbudget.conf.settings.test': Environments.TEST
    }
    django_settings_module = os.getenv(
        'DJANGO_SETTINGS_MODULE', 'greenbudget.conf.settings.prod')
    return mapping[django_settings_module]


class ConfigError(Exception):
    pass


class ConfigInvalidError(ConfigError):

    def __init__(self, config_name, message=None):
        self.config_name = config_name
        self.message = message

    def __str__(self):
        if self.message is None:
            return f"The {self.config_name} environment variable is invalid."
        return f"The {self.config_name} environment variable is invalid: {self.message}"  # noqa


class ConfigRequiredError(ConfigError):

    def __init__(self, config_name):
        self.config_name = config_name

    def __str__(self):
        return f"{self.config_name} is a required environment variable."


ConfigOption = collections.namedtuple('ConfigOption', ['param', 'default'])


class ConfigOptions:
    options = [
        ConfigOption(param='default', default=''),
        ConfigOption(param='required', default=False),
        ConfigOption(param='validate', default=None),
        ConfigOption(param='cast', default=str),
        ConfigOption(param='cast_kwargs', default=None)
    ]

    def __init__(self, *args, **kwargs):
        data = dict(*args, **kwargs)

        # Make sure there are no unrecognized options provided.
        unrecognized = [
            k for k, _ in data.items()
            if k not in [o.param for o in self.options]
        ]
        if unrecognized:
            humanized = humanize_list(unrecognized)
            raise ConfigError(
                f"Unrecognized configuration option(s) {humanized}.")

        for option in self.options:
            setattr(self, option.param, data.get(option.param, option.default))

    def __dict__(self):
        return {o.param: getattr(self, o.param) for o in self.options}

    def clone(self, *args, **kwargs):
        current_data = self.__dict__()
        current_data.update(dict(*args, **kwargs))
        return self.__class__(current_data)

    @classmethod
    def pluck(cls, *args, **kwargs):
        data = dict(*args, **kwargs)
        other_kwargs = copy.deepcopy(data)
        option_kwargs = {}
        for option in cls.options:
            if option.param in other_kwargs:
                # Remove the configuration parameter so that it is not returned
                # in the set of non-configuration parameters.
                option_kwargs[option.param] = other_kwargs.pop(option.param)
        return cls(**option_kwargs), other_kwargs


class MultipleConfig:
    def __init__(self, *args, **kwargs):
        data = dict(*args, **kwargs)
        for k, v in data.items():
            setattr(self, k, v)


class Config:
    """
    Manages the loading of configuration parameters from a shell environment or
    local .env file, the name for which can be overriden by exporting
    DOTENV_PATH in your shell.
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

    def __call__(self, name, *args, **kwargs):
        """
        Reads the configuration parameter defined by `name` from the local
        .env file.  The value is then parsed and validated, and the validated,
        parsed value is returned.

        Parameters:
        ----------
        name: :obj:`str`
            The name of the configuration parameter to be read from the .env
            file.

        default: :obj:`str`, :obj:`int`, :obj:`float` or :obj:`dict` (optional)
            The default value that should be used for the configuration
            parameter in the case that the configuration parameter is not
            defined in the .env file.  If provided as a :obj:`dict`, the
            default will be looked up based on the current environment.

            Default: ""

        required: :obj:`boolean`, :obj:`list`, :obj:`tuple` or :obj:`dict` (optional)  # noqa
            Whether or not the configuration parameter is required.
            If provided as a :obj:`dict`, whether or not the parameter is
            required will be determined based on the key of the :obj:`dict`
            that is associated with the current environment.
            If provied as an iterable, whether or not the parameter is required
            will be determined based on whether or not the current environment
            is in the provided iterable.

            Default: False

        validate: :obj:`lambda` (optional)
            An additional validate method that should be used to validate the
            configuration parameter value read from the .env file.

            Default: None

        cast: :obj:`type` (optional)
            The type that the raw configuration parameter value should be cast
            to.

            Default: str

        cast_kwargs: :obj:`dict` (optional)
            If applicable, the keyword arguments that should be included in
            the call to the function defined by the `cast` argument.

            Default: None
        """
        if args:
            if len(args) == 1 and isinstance(args[0], ConfigOptions):
                options = args[0]
            else:
                raise TypeError("Invalid inclusion of configuration options.")
        else:
            options = ConfigOptions(**kwargs)

        # Whether or not the configuration is required can be a function of
        # the environment we are in, specified as either a dict or an iterable.
        required = options.required
        if isinstance(options.required, dict):
            required = required.get(self._environment, False)

        elif (not isinstance(required, str)
                and hasattr(required, '__iter__')):
            required = self._environment in required

        # The configuration default can be a function of what environment we
        # are in.
        default = options.default
        if isinstance(default, dict):
            default = default.get(self._environment, '')

        name = name.upper()
        if name not in self._values:
            value = os.getenv(name, default)
            if value is None:
                self._values[name] = self._defaults[name] = default
            else:
                v = self._cast_value(name, value, options)
                if options.validate is not None:
                    self.validate(name, v, options.validate)
                self._values[name] = v

            if required and not self._values[name]:
                raise ConfigRequiredError(name)

        return self._values[name]

    def multiple(self, *args, **kwargs):
        """
        Reads multiple configuration parameters, defined by the keys of
        the providing mapping, from the local .env file.  Each parameter
        and its associated value is then parsed and validated, and an object
        containing the parameter names as attributes is returned.
        """
        # Separate out the top level options that will apply to all parameters
        # being read from the mapping of parameters to individual parameter
        # level options.
        options, mapping = ConfigOptions.pluck(*args, **kwargs)

        multiple_configuration = {}
        for k, v in mapping.items():
            # Merge the top level options with the options provided for just
            # the single configuration param.
            if v is not None and not isinstance(v, dict):
                raise ConfigError(
                    "A mapping must be provided for each parameter.")
            name = k
            if v is not None:
                name = v.pop('name', k)
                cloned = options.clone(v)
            else:
                cloned = options.clone()
            multiple_configuration[k] = self.__call__(name, cloned)
        return MultipleConfig(**multiple_configuration)

    def validate(self, name, value, validator):
        """
        Validates the value read from the .env file based on the validator
        function provided.
        """
        if not hasattr(validator, '__call__'):
            raise ConfigError("Validator must be a callable.")

        validated = validator(value)
        if isinstance(validated, tuple):
            if len(validated) not in (1, 2):
                raise ConfigError(
                    "Validation must return a tuple of length 1 or 2.")

            is_valid = validated[0]
            if is_valid is not True:
                if len(validated) == 2:
                    raise ConfigInvalidError(name, message=validated[1])
                raise ConfigInvalidError(name)

        elif validated is not True:
            raise ConfigInvalidError(name)

    def _cast_value(self, name, value, options):
        """
        Casts the value read from the .env file to a specific type for a
        specific configuration parameter.

        Parameters:
        ----------
        name: :obj:`str`
            The name of the configuration parameter read from the .env file.
        value: :obj:`str`
            The raw value of the configuration parameter read from the .env
            file.
        options: :obj:`ConfigOptions`
            The set of :obj:`ConfigOptions` provided for the current parameter.
        """
        cast_kwargs = options.cast_kwargs or {}
        if options.cast is None:
            return value
        elif not hasattr(options.cast, '__call__'):
            raise ConfigInvalidError(name, message="Cast must be a callable.")
        try:
            return options.cast(value, **cast_kwargs)
        except ValueError:
            raise ConfigInvalidError(name, message="Could not cast value.")

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
