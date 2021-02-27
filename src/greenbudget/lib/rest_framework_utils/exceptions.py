from rest_framework import exceptions
from django.utils.translation import gettext_lazy as _


def _consolidate_field_errors(fields, message):
    error = {}
    for field in fields:
        error[field] = message
    return error


class CommonErrorCodes(object):
    REQUIRED = "required"
    INVALID = "invalid"


class AbstractFieldError(exceptions.ValidationError):
    def __init__(self, *args, **kwargs):
        # pylint: disable=no-member
        message = _(kwargs.pop("message", self.default_message))
        if len(args) > 1:
            super().__init__(_consolidate_field_errors(args, message), **kwargs)
        else:
            try:
                field = args[0]
            except IndexError:
                raise ValueError(
                    "The exception must be provided at least 1 field.")
            else:
                if (hasattr(field, '__iter__')
                        and not isinstance(field, str)):
                    if len(field) > 1:
                        super().__init__(
                            _consolidate_field_errors(field, message),
                            **kwargs)
                    else:
                        super().__init__({field[0]: [message]}, **kwargs)
                else:
                    super().__init__({field: [message]}, **kwargs)


class RequiredFieldError(AbstractFieldError):
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

    Usage:
    -----
    >>> raise RequiredFieldError("foo") or raise RequiredFieldError(["foo])
    >>> RESPONSE [400]
    >>>    {
    >>>        "errors": {
    >>>            "foo": [{
    >>>                 "message": "This field is required.",
    >>>                 "code": "required"
    >>>             }]
    >>>         }
    >>>    }

    >>> raise RequiredFieldError("foo", "bar")
    >>>     or raise RequiredFieldError(["foo", "bar"])
    >>> RESPONSE [400]
    >>>    {
    >>>        "errors": {
    >>>            "foo": [{
    >>>                 "message": "This field is required.",
    >>>                 "code": "required"
    >>>             }]
    >>>            "bar": [{
    >>>                 "message": "This field is required.",
    >>>                 "code": "required"
    >>>             }]
    >>>         }
    >>>    }
    """
    default_code = CommonErrorCodes.REQUIRED
    default_message = "This field is required."


class InvalidFieldError(AbstractFieldError):
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

    Usage:
    -----
    >>> raise InvalidFieldError("foo") or raise InvalidFieldError(["foo])
    >>> RESPONSE [400]
    >>>    {
    >>>        "errors": {
    >>>            "foo": [{
    >>>                 "message": "This field is invalid.",
    >>>                 "code": "invalid"
    >>>             }]
    >>>         }
    >>>    }

    >>> raise InvalidFieldError("foo", "bar")
    >>>     or raise InvalidFieldError(["foo", "bar])
    >>> RESPONSE [400]
    >>>    {
    >>>        "errors": {
    >>>            "foo": [{
    >>>                 "message": "This field is invalid.",
    >>>                 "code": "invalid"
    >>>             }]
    >>>            "bar": [{
    >>>                 "message": "This field is invalid.",
    >>>                 "code": "invalidv"
    >>>             }]
    >>>         }
    >>>    }
    """
    default_code = CommonErrorCodes.INVALID
    default_message = "This field is invalid."
