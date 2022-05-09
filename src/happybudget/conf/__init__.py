import collections
import copy
import csv
import functools
import inspect
import logging
import os
import pathlib
import sys

from dotenv import load_dotenv

from django.utils.functional import SimpleLazyObject

from happybudget.lib.utils import humanize_list


logger = logging.getLogger('happybudget')


def get_lazy_setting(func):
    # pylint: disable=import-outside-toplevel
    from django.conf import settings
    return func(settings)


def LazySetting(func):
    return SimpleLazyObject(lambda: get_lazy_setting(func))


class Environments:
    PROD = "Production"
    DEV = "Development"
    TEST = "Test"
    LOCAL = "Local"


def get_environment():
    mapping = {
        'happybudget.conf.settings.dev': Environments.DEV,
        'happybudget.conf.settings.local': Environments.LOCAL,
        'happybudget.conf.settings.prod': Environments.PROD,
        'happybudget.conf.settings.test': Environments.TEST
    }
    django_settings_module = os.getenv(
        'DJANGO_SETTINGS_MODULE', 'happybudget.conf.settings.prod')
    return mapping[django_settings_module]


class suppress_with_setting:
    """
    Decorator that decorates a given function or class such that the function
    implementation or class initialization will be suppressed when the provided
    setting attribute evaluates to the provided value, which defaults to
    `False`.

    In the case when this decorator is applied to a class, the decorator will
    apply to the class's __init__ method, which means we cannot return a value
    and the only option is to raise an exception.  This means that the
    `return_value` argument does not apply.

    Parameters:
    ----------
    attr: :obj:`str`
        The settings attribute that exists on the Django settings object
        :obj:`django.conf.settings` whose value dictates whether or not the
        decorating function should be suppressed.

    value: (optional)
        The value of the settings attribute defined by `attr` that, when
        consistent with the actual value of of the settings attribute defined
        by `attr`, should cause the function to be suppressed.

        Default: False

    return_value: (optional)
        The value that the function should return when it is suppressed. Only
        applicable when the decorator is decorating a function, not a class.

        Default: None

    exc: :obj:`str` or :obj:`bool` (optional)
        If it is desired that the function should raise an exception instead of
        return a value when it is suppressed, this parameter can be specified.

        If it is specified as `True`, :obj:`ConfigSuppressionError` will be
        raised with a generic message.  If the value is a :obj:`str`,
        :obj:`ConfigSuppressionError` will be raised with the value as its
        message.

        In the case that the decorator is being applied to a class, the
        exception will always be raised on initialization of the class.

        Default: None
    """
    def __init__(self, attr, **kwargs):
        self._attr = attr
        self._value = kwargs.pop('value', False)
        self._return_value = kwargs.pop('return_value', None)
        self._exc = kwargs.pop('exc', None)

    def __call__(self, func):
        def func_inner(*args, **kwargs):
            if not self.is_suppressed():
                return func(*args, **kwargs)
            # In the case that we are decorating a function, raising an
            # exception is not the default behavior.
            if self._exc is True or isinstance(self._exc, str):
                self._raise_suppressed(func=func)
            logger.warning("Skipping call to %s because %s = %s." % (
                func.__name__,
                self._attr,
                self.current_value()
            ))
            return self._return_value

        # In the case that we are decorating a class, we want to override the
        # __init__ method to check if it is suppressed before allowing the
        # class to initialize.  Raising an exception is the only allowed
        # behavior.
        if inspect.isclass(func):
            original_init = func.__init__

            def new_init(instance, *args, **kwargs):
                if self.is_suppressed():
                    self._raise_suppressed(klass=func)
                original_init(instance, *args, **kwargs)
            setattr(func, '__init__', new_init)
            return func

        return functools.wraps(func)(func_inner)

    def _raise_suppressed(self, **kwargs):
        raise ConfigSuppressionError(
            attr=self._attr,
            message=self._exc if isinstance(self._exc, str) else None,
            **kwargs
        )

    @classmethod
    def raise_suppressed(cls, attr, message=None, func=None, klass=None):
        cls(attr, exc=message)._raise_suppressed(func=func, klass=klass)

    @classmethod
    def raise_if_suppressed(cls, attr, message=None, **kwargs):
        instance = cls(attr, exc=message)
        if instance.is_suppressed():
            cls.raise_suppressed(attr, message=message, **kwargs)

    def current_value(self):
        # It is important here that the settings object is dynamically
        # imported.
        # pylint: disable=import-outside-toplevel
        from django.conf import settings
        return getattr(settings, self._attr)

    def is_suppressed(self):
        return self.current_value() == self._value


class ConfigError(Exception):
    pass


class ConfigSuppressionError(ConfigError):
    obj_refs = ['func', 'klass', 'obj']

    def __init__(self, attr, message=None, **kwargs):
        self.attr = attr
        self.message = message

        assert self.message is not None \
            or any([x in kwargs for x in self.obj_refs]), \
            "Either the function or class being suppressed must be provided " \
            "if the message is not provided explicitly."
        for ref in self.obj_refs:
            setattr(self, f'_{ref}', kwargs.get(ref))

    @property
    def func_or_cls(self):
        for ref in self.obj_refs:
            if getattr(self, f'_{ref}') is not None:
                return getattr(self, f'_{ref}')
        raise Exception("Improperly configured initialization of exception.")

    @property
    def reference_name(self):
        if not isinstance(self.func_or_cls, str):
            if inspect.isclass(self.func_or_cls):
                return 'class'
            return 'function'
        elif self._func is not None:
            return 'function'
        elif self._klass is not None:
            return 'class'
        return 'object'

    def __str__(self):
        if self.message is not None:
            return self.message
        # The function or class can also be provided as a string name.
        obj_name = getattr(self.func_or_cls, '__name__', self.func_or_cls)
        return (
            f"The {self.reference_name} {obj_name} is suppressed due to the "
            f"value of configuration parameter {self.attr}."
        )


class ConfigInvalidError(ConfigError):

    def __init__(self, config_name, message=None):
        self.config_name = config_name
        self.message = message

    def __str__(self):
        if self.message is None:
            return f"The {self.config_name} environment variable is invalid."
        return (
            f"The {self.config_name} environment variable is invalid: "
            "{self.message}"
        )


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
        ConfigOption(param='cast_kwargs', default=None),
        ConfigOption(param='enabled', default=True),
        ConfigOption(param='disabled_value', default=None)
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
        # pylint: disable=not-callable
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
            defined in the .env file.

            If provided as a :obj:`dict`, the default will be looked up based on
            the current environment.

            Default: ""

        enabled: :obj:`bool` (optional)
            If False, the configuration will be treated as disabled - and an
            attempt to lookup the value in the .env file will not be made.

            The configuration value will return as the value defined by the
            parameter `disabled_value`, which defaults to `None`.

            Default: True

        disabled_value (optional)
            If the parameter defined by `enabled` indicates that the
            configuration is disabled, this value will be returned for the
            configuration.

            Default: None

        required: :obj:`boolean`, :obj:`list`, :obj:`tuple` or :obj:`dict`
            (optional)
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

        # If the configuration is disabled, simply return the `disabled_value`,
        # which will be `None` unless otherwise specified.
        enabled = options.enabled
        if not enabled:
            return options.disabled_value

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
        except ValueError as e:
            raise ConfigInvalidError(
                name, message="Could not cast value.") from e

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
