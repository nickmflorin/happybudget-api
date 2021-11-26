from rest_framework import exceptions
from django.utils.translation import gettext_lazy as _

from greenbudget.lib.utils import ensure_iterable, get_string_formatted_kwargs


def _consolidate_field_errors(fields, message):
    error = {}
    for field in fields:
        error[field] = message
    return error


class CommonErrorCodes(object):
    REQUIRED = "required"
    INVALID = "invalid"


class ValidationError(exceptions.ValidationError):
    """
    An extension of DRF's :obj:`rest_framework.exceptions.ValidationError` that
    allows us to more flexibly indicate the internal type of the ValidationError
    (global or field) and the specific fields that caused the ValidationError
    outside of the context of a `validate_x` method on the serializer.

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

    However, sometimes we manually want to indicate the same error, outside
    the context of a field level validation method on the serializer, but want
    to do so in the standard/consistent way that DRF does.

    Additionally, this extension allows an additional property,
    `default_info_detail`, to be specified on the Exception class as a string
    with formatting keyword arguments.  If all of the formatting keyword
    arguments are present in the arguments supplied to the Exception on
    __init__, the detail message will render as that string formatted with
    the provided arguments.
    """

    def __init__(self, *args, **kwargs):
        data = _(kwargs.pop("message", self.default_detail))

        fields = ensure_iterable(kwargs.pop('field', None))
        if args:
            fields = ensure_iterable(args[0])
            if len(args) > 1:
                fields = list(args)

        if not hasattr(self, 'error_type'):
            self.error_type = 'field' if fields else 'global'

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
                    data = exceptions.ErrorDetail(
                        _(self.default_info_detail.format(**format_kwargs)),
                        code=kwargs.get('code', self.default_code)
                    )
                    if fields:
                        data = _consolidate_field_errors(fields, data)
        elif fields:
            data = _consolidate_field_errors(fields, data)

        super().__init__(data, **kwargs)


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
    default_code = CommonErrorCodes.REQUIRED
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
    default_code = CommonErrorCodes.INVALID
    default_detail = "This field is invalid."
