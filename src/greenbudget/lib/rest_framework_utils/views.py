from collections.abc import Mapping
import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404

from rest_framework import views, exceptions
from rest_framework.response import Response
from rest_framework.serializers import as_serializer_error
from rest_framework_simplejwt.exceptions import AuthenticationFailed

from greenbudget.lib.utils import concat


logger = logging.getLogger('greenbudget')


def exception_handler(exc, context):
    """
    A custom exception handler standardizes responses when errors occur.

    This custom behavior is a small tweak to DRF's REST exception handling
    protocols - with the purpose of making things simpler in the frontend.

    The behavior that is added on top of django-rest-framework's default
    exception_handler is the following:

    (1) Includes both the ValidationError messages and error codes.

        By default, if you raise a ValidationError when validating a field,
        django-rest-framework will not include the code in the response.  For
        example, if we raise the following:

        >>> raise ValidationError('Username is invalid', code='invalid')

        django-rest-framework will return a response with status code 400 and
        response body {"username": ["Username is invalid"]}.  In many cases, the
        frontend will need to know what the error code is, so that it can
        determine which error message to display.

        For this reason, this error handler will format the response as:

        {"errors": [{
            "username": [{"message": "Username is invalid", "code": "invalid"}]
        }]}

    (2) Treats authentication errors as their own subset.

        If an :obj:`rest_framework.exceptions.AuthenticationFailed` is raised,
        the default behavior will be rendering an error in the response that
        looks like:

        {"errors": {"__all__": [{"message": ..., "code": ... }]}}

        We want to make those errors more distinct for the frontend, so they
        are rendered as:

        {"errors": {"auth": [{"message": ..., "code": ... }]}}

    (3) Simplifies errors in regard to ManyToManyField(s).

        If submitting a POST request to update an object that has a M2M field,
        the M2M instances to associate with the object being created can be
        included as a list of PK's (i.e. POST /users {groups: [1, 4]})

        If there is an error with any of the associated groups, DRF will not
        only include the error but it will be indexed by the index of the
        problematic element in the array.

        >>> {'errors': {'groups': {1: [{'message': ..., 'code': ...}]}}}

        This can make things confusing in the frontend, so we collapse it to:

        >>> {'errors': {'groups': [{'message': ..., 'code': ...}]}}

    (4) Consistent handling of 404 errors.

        By default, DRF will catch Django Http404 and render a response such as:

        >>> { "detail": "Not found." }

        We want to keep those consistent with other DRF exceptions (not Django
        exceptions) by rendering a response as:

        >>> {'errors': {'__all__': [{'message': 'Not found', 'code': 'not_found'}]}}  # noqa

    (5) Allows for extra data to be attributed to the exception and returned in
        the response.

    (6) Allows the exception to include information triggering a database
        rollback for the transactions that occured within a view.

    Note:
    ----
    This is not currently activated because there are mixins that are being
    used to bypass the Django REST Framework default exception handling.  Once
    those are removed, this will be active.
    """
    # In case a Django ValidationError is raised outside of a serializer's
    # validation methods (as might happen if we don't know the validation error
    # until we send a request to a third party API), convert to a DRF
    # ValidationError.
    if isinstance(exc, DjangoValidationError):
        exc = exceptions.ValidationError(detail=as_serializer_error(exc))

    # By default, Django REST Framework will catch Http404 and return a response
    # { "detail": "Not found." }.  We want to include a code for the frontend.
    elif isinstance(exc, Http404):
        message = str(exc) or 'The requested resource could not be found.'
        data = {
            'errors': {
                '__all__': [{
                    'message': message,
                    'code': 'not_found'
                }]
            }
        }
        logger.warning("There was a user error", extra=data)
        return Response(data, status=404)

    # If the exception is not an instance of exceptions.APIException, allow
    # the original django-rest-framework exception handler to handle the
    # exception.
    elif not isinstance(exc, exceptions.APIException):
        return views.exception_handler(exc, context)

    elif isinstance(exc, AuthenticationFailed):
        data = {'auth': [exc.get_full_details()]}

    elif isinstance(exc.detail, (list, dict)):
        data = exc.get_full_details()
        if exc.status_code == 404 and '__all__' in data:
            data['__all__'][0]['code'] == 'not_found'
        elif exc.status_code == 400:
            # See Point(3) in Docstring
            if isinstance(data, dict):
                for field, errors in data.items():
                    if (isinstance(errors, dict)
                            and all([
                                isinstance(k, int) and isinstance(v, list)
                                for k, v in errors.items()
                            ])):
                        data[field] = concat([v for _, v in errors.items()])
        # Keep things consistent by still referencing the list of errors as
        # the global errors.
        if isinstance(data, list):
            data = {'__all__': data}
    else:
        data = {'__all__': [exc.get_full_details()]}

    response_data = {'errors': data}

    # Allow the exception to include extra data that will be attributed to the
    # response.
    if isinstance(getattr(exc, 'extra', None), Mapping):
        response_data.update({k: v for k, v in exc.extra.items()})

    logger.info("There was a user error", extra=response_data)
    return Response(response_data, status=exc.status_code)
