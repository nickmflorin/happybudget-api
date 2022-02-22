import functools

from greenbudget.lib.utils import (
    ensure_iterable, empty, conditionally_format_string)
from greenbudget.app.user.models import User


class ValidationMessageMixin:
    default_message = 'Invalid value'

    def __init__(self, message=None):
        self._message = message

    def get_message(self, value, message=None, **kwargs):
        msg = message or self._message or self.default_message
        if hasattr(msg, '__call__'):
            return msg(value)
        return conditionally_format_string(msg, value=value, **kwargs)


class ValidationFailed(Exception, ValidationMessageMixin):
    def __init__(self, value, message=None):
        Exception.__init__(self)
        self._value = value
        ValidationMessageMixin.__init__(self, message)

    @property
    def message(self):
        return self.get_message()

    def __str__(self):
        return self.message

    def get_message(self, **kwargs):
        return super().get_message(self._value, **kwargs)


class Validator(ValidationMessageMixin):
    def __init__(self, *args, **kwargs):
        self._func = kwargs.pop('func', None)
        self._test = 5
        if self._func is None and len(args) != 0 \
                and hasattr(args[0], '__call__'):
            self._func = args[0]
        super().__init__(**kwargs)

    def validate(self, value):
        return value

    def __call__(self, value):
        if self._func is not None:
            result = self._func(value)
        else:
            result = self.validate(value)
        if result is None or result is True:
            return value
        elif result is False:
            self.fail(value)
        return result

    def fail(self, value, **kwargs):
        msg = self.get_message(value, **kwargs)
        raise ValidationFailed(value, msg)


class IntegerValidator(Validator):
    def validate(self, value):
        try:
            return int(value)
        except ValueError:
            self.fail(f"Value {value} is not a valid integer.")


class ModelExistsValidator(Validator):
    default_message = "{model_cls} does not exist."

    def __init__(self, model_cls, attr, **kwargs):
        super().__init__(**kwargs)
        self._attr = attr
        self._model_cls = model_cls

    @property
    def model_cls(self):
        return self._model_cls

    @property
    def attr(self):
        return self._attr

    def validate(self, value):
        kwargs = {self.attr: value}
        try:
            return self.model_cls.objects.get(**kwargs)
        except self.model_cls.DoesNotExist:
            self.fail(value, model_cls=self._model_cls.__name__)


class Query:
    default_validators = []

    def __init__(self, command, **kwargs):
        self.command = command
        self._prompt = kwargs.pop('prompt', None)
        self._prefix = kwargs.pop('prefix', None)
        self._default = kwargs.pop('default', empty)
        self._required = kwargs.pop('required', empty)
        self._validators = ensure_iterable(kwargs.pop('validators', None))
        if hasattr(self, 'default_validators'):
            self._validators += getattr(self, 'default_validators')

    def __call__(self):
        if self._prompt:
            self.command.prompt(self._prompt)
        try:
            while True:
                try:
                    value = self.get_value()
                except ValidationFailed as e:
                    self.notify_failure(e)
                else:
                    try:
                        vs = self.perform_validation(value)
                    except ValidationFailed as e:
                        self.notify_failure(e)
                    else:
                        return vs
        except KeyboardInterrupt:
            pass

    @property
    def prefix(self):
        return self._prefix or "Value"

    @property
    def full_prefix(self):
        if self.default is empty:
            return f"{self.prefix}: "
        return f"{self.prefix} (press Enter for {self.default}): "

    def get_input(self):
        return input(self.full_prefix)

    @property
    def required(self):
        return self._required

    @property
    def default(self):
        return self._default

    def get_value(self):
        raw_value = self.get_input()
        if raw_value.strip() == "":
            if self.required is True \
                    or (self.required is empty and self.default is empty):
                raise ValidationFailed(
                    raw_value, message="This value is required.")
            elif self.default is empty:
                return None
            return self.default
        return raw_value

    def notify_failure(self, data):
        message = data.message
        if not message.endswith('.'):
            message = f"{message}."
        message = f"{message} Please try again."
        self.command.prompt(message, style_func="ERROR")

    def fail(self, *args, **kwargs):
        raise ValidationFailed(*args, **kwargs)

    def perform_validation(self, value):
        for v in self.validators:
            value = v(value)
        return value

    @property
    def validators(self):
        vs = self.default_validators[:]
        for v in self._validators:
            if isinstance(v, Validator) or hasattr(v, '__call__'):
                vs.append(v)
            elif isinstance(v, (list, tuple)):
                assert len(v) == 2, \
                    "Invalid validator provided.  Must be an iterable of " \
                    "length 2, with the first element being the validation " \
                    "function and the second being the error message."
                vs.append(Validator(v[0], message=v[1]))
            else:
                raise Exception(
                    "Invalid validator provided.  Must be an iterable of "
                    "length 2, a validation function or an instance of "
                    f"{Validator}."
                )
        return vs


class IntegerQuery(Query):
    default_validators = [IntegerValidator()]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._max_value = kwargs.pop('max_value', None)

    @property
    def validators(self):
        vs = super().validators
        if self._max_value is not None:
            return vs + [Validator(
                func=lambda v: v <= self._max_value,
                message=lambda v:
                f"Value {v} exceeds max value {self._max_value}."
            )]
        return vs


class ModelQuery(Query):
    default_attr = 'pk'
    does_not_exist_message = "{model_cls} does not exist."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._attr = kwargs.pop('attr', None)
        self._model_cls = kwargs.pop(
            'model_cls', getattr(self, 'model_cls', None))
        if self._model_cls is None:
            raise Exception("The model class must be defined.")

    @property
    def default_validators(self):
        return [ModelExistsValidator(self.model_cls, self.attr)]

    @property
    def model_cls(self):
        return self._model_cls

    @property
    def attr(self):
        return self._attr or self.default_attr

    @property
    def prefix(self):
        return self._prefix or f"{self._model_cls.__name__} ({self.attr})"


class UserQuery(ModelQuery):
    default_attr = 'email'
    model_cls = User


def query_and_include(param, **kwargs):
    query_cls = kwargs.pop('query_cls', Query)

    def decorator(func):
        @functools.wraps(func)
        def inner(command, *a, **kw):
            query_instance = query_cls(command, **kwargs)
            value = query_instance()
            kw.update(**{param: value})
            return func(command, *a, **kw)
        return inner
    return decorator


def query_and_include_integer(param, **kwargs):
    kwargs.setdefault('query_cls', IntegerQuery)
    return query_and_include(param, **kwargs)


def query_and_include_user(**kwargs):
    kwargs.setdefault('query_cls', UserQuery)
    param = kwargs.pop('param', 'user')
    return query_and_include(param, **kwargs)
