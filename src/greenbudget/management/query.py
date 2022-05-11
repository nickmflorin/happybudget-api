import functools

from happybudget.lib.utils import ensure_iterable, empty
from happybudget.app.user.models import User

from .validators import (
    ValidationFailed, Validator, IntegerValidator, ModelExistsValidator,
    BooleanValidator)


class IncludedQuery:
    """
    A decorator that will include the query information for the provided
    subclass of :obj:`Query` in the function call arguments.
    """

    def __init__(self, query_cls, param, **kwargs):
        self._query_cls = query_cls
        self._param = param
        self._query_on_confirm = kwargs.pop('query_on_confirm', None)
        self._unconfirmed_value = kwargs.pop('unconfirmed_value', empty)
        if self._query_on_confirm is not None \
                and not hasattr(query_cls, 'confirmation_value'):
            raise Exception(
                "Query class {query_cls.__name__} does not support query on "
                "confirmation."
            )
        self._kwargs = kwargs

    def __call__(self, func):
        @functools.wraps(func)
        def inner(command, *a, **kw):
            kw.update(**self.get_query_data(command))
            return func(command, *a, **kw)
        return inner

    def get_query_data(self, command):
        query_instance = self._query_cls(command=command, **self._kwargs)
        value = query_instance.__call__()
        data = {self._param: value}
        if self._query_on_confirm is not None:
            assert hasattr(self._query_cls, 'confirmation_value')
            if value == self._query_cls.confirmation_value:
                data.update(self._query_on_confirm.get_query_data(command))
            elif self._query_on_confirm._unconfirmed_value is not empty:
                data.update(**{
                    self._query_on_confirm._param:
                    self._query_on_confirm._unconfirmed_value
                })
        return data


class BaseQuery:
    default_validators = []
    Validator = Validator

    def __init__(self, **kwargs):
        self._command = kwargs.pop('command', None)
        self._prompt = kwargs.pop('prompt', None)
        self._prefix = kwargs.pop('prefix', None)
        self._default = kwargs.pop('default', empty)
        self._required = kwargs.pop('required', empty)
        self._validators = ensure_iterable(kwargs.pop('validators', None))

    def __call__(self, command=None):
        if command is not None:
            self._command = command

        if self._prompt:
            self.command.prompt(self._prompt)
        try:
            while True:
                try:
                    value, was_defaulted = self.get_value()
                except ValidationFailed as e:
                    self.notify_failure(e)
                else:
                    # This assumes that the default value provided would pass
                    # validation.
                    if was_defaulted:
                        return value
                    try:
                        vs = self.perform_validation(value)
                    except ValidationFailed as e:
                        self.notify_failure(e)
                    else:
                        return vs
        except KeyboardInterrupt:
            pass

    @property
    def command(self):
        if self._command is None:
            raise Exception(
                "Query cannot be performed until attributed to a command.")
        return self._command

    @property
    def prefix(self):
        if self._prefix is None:
            return getattr(self, 'default_prefix', "Value")
        return self._prefix

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
                return None, False
            return self.default, True
        return raw_value, False

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

    @classmethod
    def include(cls, param, **kwargs):
        return IncludedQuery(cls, param, **kwargs)


class BooleanQuery(BaseQuery):
    confirmation_value = True
    default_validators = [BooleanValidator()]
    default_prefix = "(Yes/No)"


class IntegerQuery(BaseQuery):
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


class ModelQuery(BaseQuery):
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

    @classmethod
    def include(cls, param='user', **kwargs):
        return super(UserQuery, cls).include(param, **kwargs)


class Query:
    Validator = Validator
    User = UserQuery
    Model = ModelQuery
    Boolean = BooleanQuery
    Integer = IntegerQuery
