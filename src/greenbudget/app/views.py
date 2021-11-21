from collections.abc import Mapping
import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404

from rest_framework import views, exceptions, viewsets
from rest_framework.response import Response
from rest_framework.serializers import as_serializer_error
from rest_framework_simplejwt.exceptions import AuthenticationFailed

from greenbudget.lib.utils import ensure_iterable
from greenbudget.lib.utils.urls import parse_ids_from_request


logger = logging.getLogger('greenbudget')


class GenericViewSet(viewsets.GenericViewSet):
    """
    An extension of `rest_framework.viewsets.GenericViewSet` that allows us
    to non intrusively and minorly manipulate the default behavior of the
    `rest_framework.viewsets.GenericViewSet` class for specific functionality
    used in this application.
    """

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(request=self.request, user=self.request.user)
        return context

    def get_permissions(self):
        """
        Overrides the default `.get_permissions()` method in order to provide
        the following (2) implementations:

        (1) Including Additional Permissions

            Typically, when you need to add a permission class to a specific
            view, you have to include the default permission classes again
            even though they should be included for every view based on the
            `DEFAULT_PERMISSION_CLASSES` setting.

            This method allows permission classes to be appended to the default
            permission classes by specifying the `extra_permission_classes`
            attribute.

        (2) Allowing Permissions to be Instantiated

            In our application, there are permissions that require configuration
            parameters on __init__, so the permission classes themselves have
            to be instantiated in the views.

            class View(viewsets.GenericViewSet):
                permission_classes = [IsAuthenticated(...options)]

            This is compared to the way that the DRF view traditionally expects
            them to be included, which is non-instantiated classes:

            class View(viewsets.GenericViewSet):
                permission_classes = [IsAuthenticated]
        """
        extra_permissions = getattr(self, 'extra_permission_classes', [])
        extra_permissions = ensure_iterable(extra_permissions)
        permissions = list(self.permission_classes)[:] + [
            p for p in extra_permissions if p not in self.permission_classes]
        permissions = [p() if isinstance(p, type) else p for p in permissions]
        return permissions


def filter_by_ids(cls):
    """
    A decorator for extensions of :obj:`rest_framework.views.ViewSet` that
    will filter the queryset by a list of IDs provided as query params in
    the URL.  Applicable for list related endpoints:
    >>> GET /budgets/<id>/accounts?ids=[1, 2, 3]
    """
    original_get_queryset = cls.get_queryset

    @property
    def request_ids(instance):
        return parse_ids_from_request(instance.request)

    def get_queryset(instance, *args, **kwargs):
        qs = original_get_queryset(instance, *args, **kwargs)
        if instance.request_ids is not None:
            qs = qs.filter(pk__in=instance.request_ids)
        return qs

    cls.request_ids = request_ids
    if original_get_queryset is not None:
        cls.get_queryset = get_queryset
    return cls


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
    (5) Inclusion of Auth Sensitive Parameters
        Currently, this pertains to two parameters:
        (1) force_logout: Informs the frontend that we need to forcefully log
            the :obj:`User` out of their session.  This applies mostly to JWT
            token validation.
            The JWT middleware will automatically include the `force_logout`
            param at the top level of the response in the case that the JWT
            validation fails on a given request:
            >>> { errors: [...], force_logout: True }
            However, we want the ability to control this more granularly on an
            Exception basis.  If an authentication related Exception has the
            attribute `force_logout = True`, here we will inform the JWT
            middleware that we still want to force logout the :obj:`User` by
            setting this parameter as an attribute on the
            :obj:`response.Response`.
            >>> setattr(response, '_force_logout', force_logout)
        (2) user_id: Informs the frontend what :obj:`User` triggered the
            authentication related exception for cases when the :obj:`User`
            is not logged in.
            This applies mostly to email confirmation, where we need to inform
            the frontend  what :obj:`User` tried to login to the system without
            actually logging them in.
            For authentication related endpoints, we can include this information
            by setting the `user_id` parameter on the Exception being raised.
            Here, we then pull that `user_id` off of the raised Exception and
            inform the JWT middleware what it's value is so that it can include
            it in the top level of the response:
            >>> { errors: [...], force_logout: True }
            We do this by setting the `user_id` param on the
            :obj:`response.Response` object:
            >>> setattr(response, '_user_id', user_id)
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

    response_data = {}
    force_logout = None

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
    elif isinstance(exc, (
        AuthenticationFailed,
        exceptions.AuthenticationFailed,
        exceptions.NotAuthenticated,
        exceptions.PermissionDenied
    )):
        error_type = getattr(exc, 'error_type', 'auth')
        kwargs = {'details': exc.detail, 'error_type': error_type}
        # If the Exception includes a `force_logout` or `user_id` param, store
        # the value so we can set it on the overall Response object for the
        # JWT middleware.
        force_logout = getattr(exc, 'force_logout', None)

        user_id = getattr(exc, 'user_id', None)
        request_user = context['request'].user

        if user_id is not None:
            response_data['user_id'] = user_id
        elif request_user.is_authenticated:
            response_data['user_id'] = request_user.pk

        data = map_details(**kwargs)

    elif isinstance(exc.detail, dict):
        default_error_type = 'field'
        if '__all__' in exc.detail:
            default_error_type = 'global'

        error_type = getattr(exc, 'error_type', default_error_type)
        data = map_exception_details(exc, error_type=error_type)

        for err in data:
            if err['error_type'] == 'global':
                assert err['field'] == '__all__', \
                    "Invalid field included for global error!"
                del err["field"]

    else:
        data = map_exception_details(exc, default_error_type='global')

    response_data['errors'] = data
    if force_logout:
        response_data['force_logout'] = True

    # Allow the exception to include extra data that will be attributed to the
    # response at the top level, not individual errors.
    if isinstance(getattr(exc, 'extra', None), Mapping):
        response_data.update({k: v for k, v in exc.extra.items()})

    logger.info("API Error", extra=response_data)

    response = Response(response_data, status=exc.status_code)

    # Include meta information on response for JWT middleware.
    setattr(response, '_force_logout', force_logout)

    return response
