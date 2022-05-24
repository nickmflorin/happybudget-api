from rest_framework import exceptions, status
from django.utils.translation import gettext_lazy as _

from happybudget.lib.utils import (
    ensure_iterable, get_string_formatted_kwargs, first_iterable_arg)


def base_exception_cls(cls):
    """
    A class decorator that should be used to decorate the base class of all
    internal instances of :obj:`rest_framework.exceptions.ApiException`.

    The class decorator allows all base class exceptions to be initialized
    or later denoted with `hard_raise` behavior - which will bypass the
    response rendering in the :obj:`happybudget.app.views.exception_handler`
    method and raise the exception, triggering a 500 response, instead of
    rendering the error in the response.

    All usages of :obj:`rest_framework.exceptions.ApiException` inside the
    application should reference a custom base exception class that extends
    the relevant exception class from rest_framework.  These custom base
    exception classes should be decorated with this decorator.
    """
    original_init = getattr(cls, '__init__')

    def __init__(instance, *args, **kwargs):
        setattr(instance, '__hard_raise__', kwargs.pop('hard_raise', False))
        original_init(instance, *args, **kwargs)

    def mark_for_hard_raise(instance, hard_raise=True):
        setattr(instance, '__hard_raise__', hard_raise)

    setattr(cls, '__init__', __init__)
    setattr(cls, 'mark_for_hard_raise', mark_for_hard_raise)
    return cls


class ErrorCodes:
    BAD_REQUEST = "bad_request"
    ACCOUNT_NOT_AUTHENTICATED = "account_not_authenticated"
    REQUIRED = "required"
    INVALID = "invalid"
    PERMISSION_ERROR = "permission_error"
    PRODUCT_PERMISSION_ERROR = "product_permission_error"


@base_exception_cls
class PermissionErr(exceptions.PermissionDenied):
    default_code = ErrorCodes.PERMISSION_ERROR


@base_exception_cls
class BadRequest(exceptions.ParseError):
    default_code = ErrorCodes.BAD_REQUEST
    default_detail = _("Bad request.")
    status_code = status.HTTP_400_BAD_REQUEST
    error_type = 'bad_request'


@base_exception_cls
class AuthenticationFailedError(exceptions.AuthenticationFailed):
    pass


@base_exception_cls
class NotAuthenticatedError(exceptions.NotAuthenticated):
    default_detail = _("User is not authenticated.")
    default_code = ErrorCodes.ACCOUNT_NOT_AUTHENTICATED
    status_code = status.HTTP_401_UNAUTHORIZED

    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop('user_id', None)
        if user_id is not None:
            setattr(self, 'user_id', user_id)
        exceptions.NotAuthenticated.__init__(self, *args, **kwargs)


@base_exception_cls
class ValidationError(exceptions.ValidationError):
    """
    An extension of DRF's :obj:`rest_framework.exceptions.ValidationError` that
    provides the following implementations:

    (1) Control of Field Level Validation

    By default, Django REST Framework will indicate that the ValidationError
    was raised in regard to a specific field when that ValidationError is
    raised inside of a serializer method that validates a specific field:

    class Serializer(serializers.ModelSerializer):
        field = serializers.CharField()

        def validate_field(self, value):
            raise exceptions.ValidationError('Invalid field.', code='invalid')

    Here, the ValidationError will render (without our custom exception
    handling view) as:

    >>> {"field":
    >>>     [{"message": "Invalid field.", "code": "invalid"}]

    However, there are cases where we want to indicate that the ValidationError
    pertained to a specific field even when raised outside of a serializer's
    field level validation method.

    This extension allows us to treat a
    :obj:`rest_framework.exceptions.ValidationError` as a validation error that
    pertains to a specific field, even when raised outside of a serializer's
    `validate_<field>` validation method, by including the `field` argument
    on initialization.

    (2) String Formatted Messages

    This extension allows subclasses to define an additional property,
    `default_info_detail`, to be defined on the class statically.  This
    property is a string that can have string formatted keyword arguments:

    >>> class MyCustomValidationError(ValidationError):
    >>>     default_info_detail = (
    >>>         "The field {field} is invalid because it has type {type}.")

    If all of the formatting keyword arguments are present in the arguments
    supplied to the exception on initialization, the exception will take on
    the message indicated by `default_info_detail` with the argument plugged
    into the string.

    >>> raise MyCustomValidationError(field='foo', type='int')
    >>> {"field": [{
    >>>     "message": "The field foo is invalid because it has type int.",
    >>>     "code": "invalid"
    >>> }]

    The exception class can be initialized in the following ways:

    - If the `field` keyword argument is supplied, the first argument will be
      the detail message.

      >>> MyCustomValidationError("This is a message.", field="foo")

      - The field argument can be provided as a single field or an iterable of
        fields:

        >>> MyCustomValidationError("This is a message.", field=("foo", "bar"))
        >>> MyCustomValidationError("This is a message.", field=["foo", "bar"])

      - If no message argument is supplied, the default detail message will be
        used.

        >>> MyCustomValidationError(field="foo")
        >>> MyCustomValidationError(field=["foo", "bar"])

    - If the `message` keyword argument is supplied, the arguments supplied
      will be treated as the fields:

      >>> MyCustomValidationError("foo", "bar", message="This is a message.")
      >>> MyCustomValidationError(["foo", "bar"], message="This is a message.")
    """
    default_code = ErrorCodes.INVALID

    def __init__(self, *args, **kwargs):
        self.fields = None
        message = self.default_detail
        if 'message' in kwargs:
            message = kwargs.pop('message')
            self.fields = first_iterable_arg(*args)
        elif 'field' in kwargs:
            self.fields = ensure_iterable(kwargs.pop('field'))
            if args:
                message = args[0]
        elif args:
            message = args[0]

        message = _(message) if isinstance(message, str) else message
        data = message

        # This ValidationError allows a default detail to be specified with
        # string formatted parameters that if provided on __init__, will be
        # used to create the error detail with the provided keyword arguments.
        if hasattr(self, 'default_info_detail') and 'message' not in kwargs:
            string_formatted_kwargs = get_string_formatted_kwargs(
                self.default_info_detail)

            if any([a in kwargs for a in string_formatted_kwargs]):
                format_kwargs = {
                    a: kwargs.pop(a, None)
                    for a in string_formatted_kwargs
                }
                if all([
                    format_kwargs[a] is not None
                    for a in string_formatted_kwargs
                ]):
                    detail = exceptions.ErrorDetail(
                        _(self.default_info_detail.format(**format_kwargs)),
                        code=kwargs.get('code', self.default_code)
                    )
                    if self.fields:
                        data = {field: detail for field in self.fields}
        elif self.fields:
            data = {field: message for field in self.fields}

        super().__init__(data, **kwargs)

    @property
    def error_type(self):
        return 'field' if self.fields else 'form'


class RequiredFieldError(ValidationError):
    """
    An exception to cleanly and consistently indicate that a field or field(s)
    is/are required and not present in the request.

    By default, Django REST Framework will indicate that a required field is
    missing based on the field definition in the serializer.  An error will
    be embedded in the response as follows:

    >>> {"field_that_was_missing":
    >>>     [{"message": "The field is required.", "code": "required"}]

    However, sometimes we manually want to indicate the same error, but want
    to do so in the standard/consistent way that DRF does.  That is when this
    `obj:RequiredFieldError` can be used.
    """
    default_code = ErrorCodes.REQUIRED
    default_detail = "This field is required."


class InvalidFieldError(ValidationError):
    """
    An exception to cleanly and consistently indicate that a field or field(s)
    is/are invalid, but present in the request.

    By default, Django REST Framework will indicate that a invalid field is
    provided based on the field definition in the serializer.  An error will
    be embedded in the response as follows:

    >>> {"field_that_was_invalid":
    >>>     [{"message": "The field is invalid.", "code": "invalid"}]

    However, sometimes we manually want to indicate the same error, but want
    to do so in the standard/consistent way that DRF does.  That is when this
    `obj:RequiredFieldError` can be used.
    """
    default_code = ErrorCodes.INVALID
    default_detail = "This field is invalid."
