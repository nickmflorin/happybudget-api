from greenbudget.lib.utils import conditionally_format_string


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


def result_in(result, values):
    """
    Checks if the validation result is in the provided set of values, accounting
    for a common discrepancy with falsey values:

    If the result value is 0, and values = [False], checking whether or not
    0 is in [False] will return True, since 0 is treated as False.  Here, do not
    want to consider 0 False but instead an integer that is not falsey:

    >>> result_value = 0
    >>> values = [None, False]
    >>> result_value in values
    >>> True

    >>> result_in(result_value, values)
    >>> False
    """
    for v in values:
        if type(v) is bool and result is v:
            return True
        elif type(v) is not bool and result == v:
            return True
    return False


class Validator(ValidationMessageMixin):
    failed_values = [False]
    indeterminate_values = [None, True]

    def __init__(self, *args, **kwargs):
        self._func = kwargs.pop('func', None)
        if self._func is None and len(args) != 0 \
                and hasattr(args[0], '__call__'):
            self._func = args[0]
        super().__init__(**kwargs)

    def __call__(self, value):
        if self._func is not None:
            result = self._func(value)
        else:
            result = self.validate(value)
        if result_in(result, self.failed_values):
            self.fail(value)
        elif result_in(result, self.indeterminate_values):
            return value
        return result

    def validate(self, value):
        return value

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


class BooleanValidator(Validator):
    failed_values = []
    indeterminate_values = [None]

    def validate(self, ans):
        return ans.lower().strip() == "yes" or ans.lower().strip() == "y"
