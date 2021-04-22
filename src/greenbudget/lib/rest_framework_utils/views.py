from collections.abc import Mapping
import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404

from rest_framework import views, exceptions
from rest_framework.response import Response
from rest_framework.serializers import as_serializer_error
from rest_framework_simplejwt.exceptions import AuthenticationFailed


logger = logging.getLogger('greenbudget')


def exception_handler(exc, context):
    """
    A custom exception handler that standardizes responses when errors occur.

    This custom behavior is a small tweak to DRF's REST exception handling
    protocols - with the purpose of making things simpler in the frontend by
    flattening out error structures into arrays.  The custom behavior also
    allows more detailed information to be provided in the response by nature of
    attributes on the :obj:`ApiException` class itself.

    The behavior that is added on top of django-rest-framework's default
    exception_handler is the following:

    (1) Inclusion of Error Codes

        By default, if you raise a ValidationError when validating a field,
        django-rest-framework will not include the code in the response.  For
        example, if we raise the following:

        >>> raise ValidationError('Username is invalid', code='invalid')

        django-rest-framework will return a response with status code 400 and
        response body

        >>> {"username": ["Username is invalid"]}

        In many cases, the frontend will need to know what the error code is,
        so that it can determine which error message to display.

        For this reason, this error handler will include the error code in the
        response.

        {"errors": [{
            "field": "username",
            "code": "invalid",
            "message": "Username is invalid.",
            "error_type": "field"
        }]}

    (2) More Consistent, Flatter Response Structure

        Typically, django-rest-framework likes to render exceptions in the
        response by indexing details by keys:

        >>> raise ValidationError('Username is invalid', code='invalid')
        >>> {"username": ["Username is invalid"]}

        This is nice, but what if we also have different errors that aren't
        necessarily relevant to an error pertaining to a specific field of a
        request payload?  We have no way of determining what the keys of the
        error response data refer to.

        For this reason, the error responses are flattened out - with each
        detail including additional context information:

        {"errors": [
           {
               "field": "username",
               "code": "invalid",
               "message": "Username is invalid.",
               "error_type": "field"
           },
           {
               "field": "email",
               "code": "invalid",
               "message": "Email is invalid.",
               "error_type": "field"
           }
        ]}

    (3) Allowing for the Inclusion of Additional Context

        Sometimes, especially in this application, we need to build errors that
        include much more information than just a code and a message.  For this
        reason, extensions of :obj:`ApiException` can be attributed with
        `detail_data` and `extra`, and if present, the data returned from these
        properties will be included in the rendered error response.

        class MyCustomValidationError(exceptions.ValidationError):
            def __init__(self, *args, **kwargs):
                self._username = kwargs.pop('username', None)
                super().__init__(*args, **kwargs)

            @property
            def extra(self):
                return {'foo': 'bar'}

            @property
            def detail_data(self):
                 return {'username': self._username}

        >>> raise MyCustomValidationError('Username is invalid', code='invalid')

        {
            "foo": "bar",
            "errors": [
                {
                    "field": "username",
                    "code": "invalid",
                    "message": "Username is invalid.",
                    "error_type": "field",
                    "username": "fakeuser@gmail.com",
                }
            ]
        }

    (4) Consistent Handling of 404 Errors.

        By default, DRF will catch Django Http404 and render a response such as:

        >>> { "detail": "Not found." }

        We want to keep those consistent with other DRF exceptions that we raise
        (not Django exceptions) by rendering a response as:

        {'errors': [{
            'message': 'Not found',
            'code': 'not_found',
            'error_type': 'http'
        }]}

    (5) Allows the exception to include information triggering a database
        rollback for the transactions that occured within a view.
    """
    def map_detail(detail, error_type, **kwargs):
        return {**{
            'message': str(detail),
            'code': detail.code,
            'error_type': error_type
        }, **kwargs}

    def map_details(details, error_type, **kwargs):
        mapped = []
        if isinstance(details, dict):
            for k, v in details.items():
                mapped += map_details(v, error_type, field=k)
        elif isinstance(details, list):
            for detail_i in details:
                if isinstance(detail_i, (list, dict)):
                    mapped += map_details(detail_i, error_type, **kwargs)
                else:
                    mapped += [map_detail(detail_i, error_type, **kwargs)]
        else:
            mapped += [map_detail(details, error_type, **kwargs)]
        return mapped

    def map_exception_details(exc, error_type=None, default_error_type='global',
            **kwargs):
        error_type = error_type or getattr(
            exc, 'error_type', default_error_type)
        detail_data = getattr(exc, 'detail_data', {})
        return map_details(exc.detail, error_type, **{**kwargs, **detail_data})

    # In case a Django ValidationError is raised outside of a serializer's
    # validation methods (as might happen if we don't know the validation error
    # until we send a request to a third party API), convert to a DRF
    # ValidationError.
    if isinstance(exc, DjangoValidationError):
        exc = exceptions.ValidationError(detail=as_serializer_error(exc))

    # By default, Django REST Framework will catch Http404 and return a response
    # { "detail": "Not found." }.  We want to include a code for the frontend.
    if isinstance(exc, Http404):
        message = str(exc) or 'The requested resource could not be found.'
        logger.warning("There was a user error", extra={
            'error_type': 'http',
            'code': 'not_found'
        })
        return Response({'errors': [
            {'message': message, 'error_type': 'http', 'code': 'not_found'}
        ]}, status=404)

    # If the exception is not an instance of exceptions.APIException, allow
    # the original django-rest-framework exception handler to handle the
    # exception.
    elif not isinstance(exc, exceptions.APIException):
        return views.exception_handler(exc, context)

    # If the user submitted a request requiring authentication and they are not
    # authenticated, include information in the context so the FE can force log
    # out the user.
    elif isinstance(exc, (AuthenticationFailed, exceptions.NotAuthenticated)):
        error_type = getattr(exc, 'error_type', 'auth')
        data = map_details(exc.detail, error_type=error_type, force_logout=True)

    elif isinstance(exc.detail, dict):
        error_type = getattr(exc, 'error_type', 'field')
        data = map_exception_details(exc, error_type=error_type)

    else:
        data = map_exception_details(exc, default_error_type='global')

    response_data = {'errors': data}

    # Allow the exception to include extra data that will be attributed to the
    # response at the top level, not individual errors.
    if isinstance(getattr(exc, 'extra', None), Mapping):
        response_data.update({k: v for k, v in exc.extra.items()})

    logger.info("There was a user error", extra=response_data)
    return Response(response_data, status=exc.status_code)
