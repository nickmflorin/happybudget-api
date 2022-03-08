from collections.abc import Mapping
import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from django.utils.functional import cached_property

from rest_framework import views, exceptions, viewsets, serializers, generics
from rest_framework.response import Response
from rest_framework.serializers import as_serializer_error
from rest_framework_simplejwt.exceptions import AuthenticationFailed

from greenbudget.lib.utils import ensure_iterable, get_nested_attribute
from greenbudget.lib.utils.urls import parse_ids_from_request

from greenbudget.app import permissions
from greenbudget.app.billing.exceptions import ProductPermissionError


logger = logging.getLogger('greenbudget')


def _get_attribute(view, attr):
    try:
        return get_nested_attribute(view, attr)
    except AttributeError:
        raise AttributeError(
            "View %s has invalid serializer class definition, "
            "serializer definition attribute %s does not exist "
            "on view." % (type(view).__name__, attr)
        )


def _evaluate_view_attribute_map(view, mapping):
    for k, v in mapping.items():
        attr = k
        iterable_lookup = False
        if attr.endswith('__in'):
            attr = attr.split('__in')[0]
            iterable_lookup = True

        attr_value = _get_attribute(view, attr)
        if iterable_lookup and attr_value not in ensure_iterable(v):
            return False
        elif not iterable_lookup and attr_value != v:
            return False
    return True


class GenericView(generics.GenericAPIView):
    """
    An extension of `rest_framework.generics.GenericAPIView` that allows us
    to non intrusively and minorly manipulate the default behavior of the
    `rest_framework.generics.GenericAPIView` class for specific functionality
    used in this application.
    """

    def check_permissions(self, request):
        permission = permissions.AND(self.get_permissions())
        permission.has_permission(request, self, raise_exception=True)

    def check_object_permissions(self, request, obj):
        permission = permissions.AND(self.get_permissions())
        permission.has_object_permission(
            request, self, obj, raise_exception=True)

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
        pm = list(self.permission_classes)[:] + [
            p for p in extra_permissions if p not in self.permission_classes]
        return permissions.instantiate_permissions(pm)

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
                return _evaluate_view_attribute_map(self, conditional)
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


class GenericViewSet(viewsets.ViewSetMixin, GenericView):
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
    In Django REST Framework, whenever an exception occurs between the time a
    request is received and a response is rendered, the exception flows through
    the exception handler.  Django REST Framework defines a default exception
    handler, but we need to customize it for purposes that are documented
    below.

    This custom exception handler standardizes responses when errors occur such
    that we can more clearly communicate details about why an error occurred and
    provide additional context, such that consumers of the API can more easily
    diagnose the source of the error and our Front End can more clearly indicate
    to a user why an error occurred.

    This custom exception handler is only concerned with customizing the behavior
    for the following (3) types of raised exceptions:

    (1) DjangoValidationError

        Django's :obj:`ValidationError` is different from Django REST Framework's
        :obj:`ValidationError`.  Django's form is meant to be used inside of
        form classes (which we do not use) and other model mechanics that
        perform validation.  In the case that we notice Django's form of the
        :obj:`ValidationError`, instead of allowing it to result in a 500
        response we simply convert it to Django REST Framework's
        :obj:`ValidationError` such that a 400 level response is returned.

    (2) Http404

        The default way in which Django REST Framework handles Django's Http404
        error is not consistent with the way in which we standardize other 400
        level errors in the response, so we intercept it and ensure that the 404
        response is standardized consistently with other 400 level responses.

    (3) ApiException

        Other than the two previous exceptions, we only want to customize the
        response behavior for exceptions that extend :obj:`ApiException`.  This
        is the baes class for all Django REST Framework exceptions.

    If any other error occurs, we simply call the default exception handler
    defined by Django REST Framework, as we are not concerned with customizing
    the response for these types of errors.

    The behavior that is added to Django REST Framework's default exception
    handling protocols includes the following:

    (1) Inclusion of Error Codes

        By default, if you raise a ValidationError during field validation, or
        in any other context, Django REST Framework will not include the code
        in the response.  For example, if we raise the following:

        >>> raise ValidationError('Username is invalid', code='invalid')

        Django REST Framework will return a response with status code 400 and
        response body

        >>> {"username": ["Username is invalid"]}

        In many cases, the Front End will need to know what the error code is,
        so that it can determine how to standardize the error message to that
        we want to display to users. Additionally, the Front End often uses
        the error codes in the response for control flow, making decisions about
        how to proceed based on the code embedded in the response.

        For this reason, this error handler will include the error code in the
        response.  So, ignoring the other fields and formatting other than the
        inclusion of the error code for now, raising the previous
        :obj:`ValidationError` will result in a 400 response with the following
        body:

        >>> {"errors": [{
        >>>    "field": "username",
        >>>    "code": "invalid",
        >>>    "message": "Username is invalid.",
        >>>    "error_type": "field"
        >>> }]}

    (2) Flatter Response Structure

        Typically, Django REST Framework likes to render responses when
        instances of :obj:`ApiException` are raised exceptions in the
        response by indexing the errors embedded in the response by keys:

        >>> class Serializer(serializers.Serializer):
        >>>     email = serializers.EmailField(...)
        >>>     username = serializers.CharField(...)
        >>>
        >>>     def validate_username(self, attrs):
        >>>         raise ValidationError('Username is invalid', code='invalid')
        >>>
        >>>     def validate_email(self, attrs):
        >>>         raise ValidationError('Email is invalid', code='invalid')

        >>> Response [400]
        >>> {"errors": {
        >>>     "username": ["Username is invalid"],
        >>>     "email": ["Email is invalid]
        >>> }}

        If the error does not pertain to a specific field (i.e. the error
        occurred during global level field validation in a serializer),
        Django REST Framework will index the error in the object embedded in
        the response by the field defined by the settings configuration
        `NON_FIELD_ERRORS_KEY` (typically "__all__"):

        >>> class Serializer(serializers.Serializer):
        >>>     def validate(self, attrs):
        >>>         raise ValidationError('Username is invalid', code='invalid')

        >>> Response [400]
        >>> {"errors": {"__all__": ["Username is invalid"]}}

        This is nice, but what if we also have different errors that aren't
        necessarily relevant to an error pertaining to a specific field of a
        request payload?  Or what if we need to automatically render the errors
        next to individual fields that may be dynamic and not known ahead of
        time?  We have no way of determining what the keys of the error response
        data refer to...

        For this reason, the errors embedded in the responses are flattened out
        into arrays - which also makes it significantly easier for the Front End
        to manage:

        >>> Response [400]
        >>> {"errors": [
        >>>   {
        >>>       "field": "username",
        >>>       "code": "invalid",
        >>>       "message": "Username is invalid.",
        >>>       "error_type": "field"
        >>>   },
        >>>   {
        >>>       "field": "email",
        >>>       "code": "invalid",
        >>>       "message": "Email is invalid.",
        >>>       "error_type": "field"
        >>>   }
        >>> ]}

        Note: The only time we will ever see multiple errors in the response
        body is when multiple field level validations failed.  For all other
        error types, there will only ever be 1 error.

    (3) Inclusion of Error Type

        By default, Django REST Framework does not give any indication of what
        type of error occurred outside of letting us know if the error that
        occurred related to a specific field or occurred outside of the context
        of a specific field (when the error is indexed by "__all__").

        In order for the Front End to better diagnose and make decisions based
        on errors embedded in the response, we develop an error type dichotomy
        that allows the Front End to categorize errors and handle them based on
        where they lie in this dichotomy.

        At the time of this writing, the dichotomy consists of the following
        error subsets:

        (1) http [404] Response or [405] Response
            Errors that are related to unexpected API configuration related
            problems, such as 404 errors or 405 errors.

        (2) field [400] Response
            Validation errors that are related to failed validation of specific
            fields in the request data.

        (3) global [400] Response
            Validation errors that are related to request data validation that
            does not pertain to a specific field in the request data.

        (4) auth [401] Response
            Validation errors related to proper authentication of a user.  These
            occur when attempting to access a protected resource without being
            authenticated or when the JWT authentication token is being
            validated. In both cases, the Front End identifies when this type
            of error is included in the response and will forcefully log out
            the user.

        (5) billing [400] Response
            Billing related errors that occur when a user is attempting to
            change, update or create subscriptions in Stripe.

        (6) permission [403] Response
            Errors raised when a user does not have the permissions to access
            a resource they are attempting to access.  These are usually avoided
            by the Front End, by only making requests when the logged in user
            has certain permissions available - but they can nonetheless occur,
            particularly when requests are submitted outside the context of our
            Front End.

        The error type of a specific error can be defined statically on the
        custom exception class.  If the custom exception class does not define
        the error type, the error type is inferred based on the error class that
        was raised in this view.

        >>> class CheckoutError(exceptions.BadRequest):
        >>>     error_type = 'billing'
        >>>     default_code = BillingErrorCodes.CHECKOUT_ERROR
        >>>     default_detail = _("There was a error during checkout.")

        >>> raise CheckoutError()
        >>> Response [400]
        >>> {"errors": [
        >>>   {
        >>>       "code": "checkout_error",
        >>>       "message": "There was an error during checkout.",
        >>>       "error_type": "billing"
        >>>   }
        >>> ]}

    (4) Allowing for the Inclusion of Additional Context

        Sometimes, especially in this application, we need to build errors that
        include much more information than just a code and a message.  Additional
        context is either included explicitly via the logic in this view or
        imlicitly via attributes defined on the custom exception class.

        (4a) Attributes Defined on the Custom Exception Class

            Extensions of :obj:`ApiException` can be attributed with
            `detail_data` and `extra`, and if present, the data returned from
            these properties will be included in the rendered error response.

            >>> class MyCustomValidationError(exceptions.ValidationError):
            >>>
            >>>    def __init__(self, *args, **kwargs):
            >>>        self._username = kwargs.pop('username', None)
            >>>        super().__init__(*args, **kwargs)
            >>>
            >>>    @property
            >>>    def extra(self):
            >>>        return {'foo': 'bar'}
            >>>
            >>>    @property
            >>>    def detail_data(self):
            >>>         return {'username': self._username}

            >>> raise MyCustomValidationError(
            >>>     'Username is invalid', code='invalid')
            >>> Response [400]
            >>> {
            >>>    "foo": "bar",
            >>>    "errors": [
            >>>        {
            >>>            "field": "username",
            >>>            "code": "invalid",
            >>>            "message": "Username is invalid.",
            >>>            "error_type": "field",
            >>>            "username": "fakeuser@gmail.com",
            >>>        }
            >>>    ]
            >>> }

        (4b) Logic in This Custom Exception Handler

            Currently, this pertains to two parameters:

            (1) user_id: Informs the frontend what :obj:`User` triggered the
                authentication related exception for cases when the :obj:`User`
                is not logged in and the exception raised was an instance of
                `greenbudget.app.authentication.exceptions.AuthenticationError`.

                This applies mostly to email confirmation, where we need to
                inform the Front End  what :obj:`User` tried to login to the
                system without actually logging them in.

                For authentication related endpoints, we can include this
                information by setting the `user_id` parameter on the Exception
                being raised. The `user_id` parameter is then pulled off of the
                raised Exception and included in the response errors:

                >>> { errors: [{ message: ..., code: ..., user_id: 5}] }

            (2) products: Informs the frontend what Stripe Products that a user
                may need to subscribe to in the case that they are trying to
                access a resource that requires a subscription to the included
                products.

                >>> { errors: [{
                >>>     message: ...,
                >>>     code: ...,
                >>>     products: ["greenbudget_standard"]
                >>> }] }

    (5) Consistent Handling of 404 Errors.

        By default, DRF will catch Django Http404 and render a response such as:

        >>> Response [404]
        >>> { "detail": "Not found." }

        We want to keep those consistent with other DRF exceptions that we raise
        (not Django exceptions) by rendering a response as:

        >>> Response [404]
        >>> {'errors': [{
        >>>    'message': 'Not found',
        >>>    'code': 'not_found',
        >>>    'error_type': 'http'
        >>> }]}
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

    def include_in_detail(data, **kwargs):
        for err in data:
            err.update(**kwargs)

    response_data = {}

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
        logger.warning("API encountered a 404 error", extra={
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

    elif isinstance(exc, (
        AuthenticationFailed,
        exceptions.AuthenticationFailed,
        exceptions.NotAuthenticated,
        exceptions.PermissionDenied
    )):
        default_error_type = 'permission' \
            if isinstance(exc, exceptions.PermissionDenied) else 'auth'

        data = map_details(
            details=exc.detail,
            error_type=getattr(exc, 'error_type', default_error_type)
        )

        # There are cases where we need to include information about the user
        # that is attempting a request when a NotAuthenticated error surfaces.
        # This mostly pertains to things like email confirmation, where we might
        # need information about the user to send a verification email in the
        # case that they cannot log in because their email is not verified.
        if isinstance(exc, exceptions.NotAuthenticated):
            user_id = getattr(exc, 'user_id', None)
            # The context user's ID will be None if it is an AnonymousUser.
            if user_id is None and context['request'].user.id is not None:
                user_id = context['request'].user.id
            if user_id is not None:
                include_in_detail(data, user_id=user_id)

        # There are cases where we need to include information about the products
        # that a user needs to be subscribed to in order to perform a certain
        # action.
        if isinstance(exc, ProductPermissionError):
            include_in_detail(
                data=data,
                products=getattr(exc, 'products'),
                permission_id=getattr(exc, 'permission_id')
            )

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

    # Allow the exception to include extra data that will be attributed to the
    # response at the top level, not individual errors.
    if isinstance(getattr(exc, 'extra', None), Mapping):
        response_data.update({k: v for k, v in exc.extra.items()})

    logger.info("API Error", extra=response_data)

    return Response(response_data, status=exc.status_code)
