from collections.abc import Mapping
import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from django.utils.functional import cached_property

from rest_framework import views, exceptions, viewsets, serializers
from rest_framework.response import Response
from rest_framework.serializers import as_serializer_error
from rest_framework_simplejwt.exceptions import AuthenticationFailed

from greenbudget.lib.utils import ensure_iterable, get_nested_attribute
from greenbudget.lib.utils.urls import parse_ids_from_request


logger = logging.getLogger('greenbudget')


def get_attribute(view, attr):
    try:
        return get_nested_attribute(view, attr)
    except AttributeError:
        raise AttributeError(
            "View %s has invalid serializer class definition, "
            "serializer definition attribute %s does not exist "
            "on view." % (type(view).__name__, attr)
        )


def evaluate_view_attribute_map(view, mapping):
    for k, v in mapping.items():
        attr = k
        iterable_lookup = False
        if attr.endswith('__in'):
            attr = attr.split('__in')[0]
            iterable_lookup = True

        attr_value = get_attribute(view, attr)
        if iterable_lookup and attr_value not in ensure_iterable(v):
            return False
        elif not iterable_lookup and attr_value != v:
            return False
    return True


class GenericViewSet(viewsets.GenericViewSet):
    """
    An extension of `rest_framework.viewsets.GenericViewSet` that allows us
    to non intrusively and minorly manipulate the default behavior of the
    `rest_framework.viewsets.GenericViewSet` class for specific functionality
    used in this application.
    """
    lookup_field = 'pk'

    @property
    def is_simple(self):
        return 'simple' in self.request.query_params

    @cached_property
    def instance(self):
        return self.get_object()

    @property
    def instance_cls(self):
        return type(self.instance)

    def _update_kwargs(self, serializer):
        kwargs = {}
        if isinstance(serializer, serializers.ModelSerializer):
            model_cls = serializer.Meta.model
            if hasattr(model_cls, 'updated_by'):
                kwargs.update(updated_by=self.request.user)
        return kwargs

    def update_kwargs(self, serializer):
        return self._update_kwargs(serializer)

    def create_kwargs(self, serializer):
        kwargs = self._update_kwargs(serializer)
        if isinstance(serializer, serializers.ModelSerializer):
            model_cls = serializer.Meta.model
            if hasattr(model_cls, 'created_by'):
                kwargs.update(created_by=self.request.user)
        return kwargs

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

    def get_serializer_class(self):
        """
        Allows the serializer class that a given instance of the view should
        use to be defined dynamically based on a set of conditionals.

        For each element of `serializer_classes`, the element must either be
        an instance of :obj:`serializers.ModelSerializer` or an iterable of
        length 2.

        (1) Instance of `serializers.ModelSerializer`

            When evaluating the `serializer_classes`, if an instance of
            :obj:`serializers.ModelSerializer` is encountered, it will be
            returned.  This is typically used for listing the default serializer
            class as the last element in `serializer_classes` such that it is
            used when none of the previous conditionals are met.

        (2) Iterable of Length 2

            When evaluating the `serializer_classes`, if an iterable is
            encountered, the decision of whether or not to use the serialializer
            class (as the second element of the iterable) is made based on
            evaluating the first element of the conditional.

            The first element of the conditional can either be a dictionary
            mapping of properties and the required values on the view instance,
            or a callback taking the view instance as it's first and only
            argument.

        Example:
        --------
        serializer_classes = (
            ({'is_simple': True}, SimpleSerializer),
            (lambda view: view.instance_cls is BaseClass, BaseSerializer)
            ({'action': 'create'}, DetailSerializer),
            RegularSerializer
        )

        Additionally, the second element of a conditional serializer can also
        be another set of conditional serializers, which will only be evaluated
        if the former first element of the upper level conditional serializer
        is True.

        Example:
        --------
        serializer_classes = (
            ({'is_simple': True}, [
                (lambda view: view.instance_cls is BaseClass, BaseSerializer)
                ({'action': 'create'}, DetailSerializer),
            ]),
        )
        """
        valid_types = (list, tuple)

        def evaluate_serializer_conditional(conditional):
            if not isinstance(conditional, dict) \
                    and not hasattr(conditional, '__call__'):
                raise ValueError(
                    "View %s has invalid serializer class definition, "
                    "serializer definition must either be of type %s "
                    "or callable."
                    % (type(self).__name__, dict)
                )
            if isinstance(conditional, dict):
                return evaluate_view_attribute_map(self, conditional)
            return conditional(self)

        def evaluate_serializer_classes(serializer_classes):
            for definition in serializer_classes:
                if not isinstance(definition, (list, tuple)) \
                        and not issubclass(
                            definition, serializers.ModelSerializer):
                    raise ValueError(
                        "View %s has invalid serializer class definition, "
                        "serializer definition must either be of types %s "
                        "or a valid subclass of %s."
                        % (
                            type(self).__name__,
                            ", ".join(["%s" % s for s in valid_types]),
                            serializers.ModelSerializer
                        )
                    )
                if isinstance(definition, valid_types):
                    if len(definition) != 2:
                        raise ValueError(
                            "View %s has invalid serializer class definition, "
                            "serializer definition must be of length 2 when "
                            "defined as an iterable." % type(self).__name__
                        )

                    if evaluate_serializer_conditional(definition[0]):
                        if isinstance(definition[1], valid_types):
                            return evaluate_serializer_classes(definition[1])
                        return definition[1]
                else:
                    # Including the serializer without any configuration
                    # conditional means that this is the default case (usually
                    # at the bottom of the array of serializer_classes) so it
                    # should be returned.
                    return definition
            return None

        if hasattr(self, 'serializer_classes'):
            evaluated = evaluate_serializer_classes(self.serializer_classes)
            if evaluated is not None:
                return evaluated

        serializer_cls = getattr(self, 'serializer_class', None)
        if serializer_cls is None:
            raise Exception(
                "View %s did not have a serializer class that met the "
                "conditional and does not define a serializer class "
                "statically." % type(self).__name__
            )
        return serializer_cls


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
