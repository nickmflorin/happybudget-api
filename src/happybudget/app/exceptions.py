from rest_framework import exceptions, status
# pylint: disable=unused-import
from rest_framework.exceptions import AuthenticationFailed  # noqa
from django.utils.translation import gettext_lazy as _

from happybudget.lib.utils import (
    ensure_iterable, get_string_formatted_kwargs, first_iterable_arg)


class BadRequestErrorCodes:
    BAD_REQUEST = "bad_request"


class BadRequest(exceptions.ParseError):
    default_code = BadRequestErrorCodes.BAD_REQUEST
    default_detail = _("Bad request.")
    status_code = status.HTTP_400_BAD_REQUEST
    error_type = 'bad_request'


class FieldErrorCodes:
    REQUIRED = "required"
    INVALID = "invalid"


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
    default_code = FieldErrorCodes.INVALID

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
        else:
            data = message

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
    default_code = FieldErrorCodes.REQUIRED
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
    default_code = FieldErrorCodes.INVALID
    default_detail = "This field is invalid."
