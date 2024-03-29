import collections
import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404

from rest_framework import views, exceptions, status
from rest_framework.response import Response
from rest_framework.serializers import as_serializer_error
from rest_framework_simplejwt.exceptions import AuthenticationFailed

from happybudget.app.billing.exceptions import (
    BillingError, ProductPermissionError)


logger = logging.getLogger('happybudget')


ErrorTypeDesignation = collections.namedtuple(
    typename='ErrorTypeDesignation',
    field_names=['exception_cls', 'error_type', 'conditional'],
    defaults=(None, )
)

DefaultErrorTypes = [
    ErrorTypeDesignation(
        exception_cls=(Http404, exceptions.MethodNotAllowed),
        error_type='http'
    ),
    ErrorTypeDesignation(
        exception_cls=exceptions.PermissionDenied,
        error_type='permission'
    ),
    ErrorTypeDesignation(exception_cls=BillingError, error_type='billing'),
    ErrorTypeDesignation(
        exception_cls=exceptions.ParseError,
        error_type='bad_request'
    ),
    ErrorTypeDesignation(
        exception_cls=exceptions.ValidationError,
        error_type='form',
        conditional=lambda e:
            isinstance(e.detail, dict) and '__all__' in e.detail
    ),
    ErrorTypeDesignation(
        exception_cls=exceptions.ValidationError,
        error_type='field',
        conditional=lambda e:
            isinstance(e.detail, dict) and '__all__' not in e.detail
    ),
    ErrorTypeDesignation(
        error_type='auth',
        exception_cls=(
            AuthenticationFailed,
            exceptions.AuthenticationFailed,
            exceptions.NotAuthenticated
        )
    )
]


def get_default_error_type(e):
    for d in DefaultErrorTypes:
        if isinstance(e, d.exception_cls) \
                and (d.conditional is None or d.conditional(e)):
            return d.error_type
    return None


def get_error_type(e):
    return getattr(e, 'error_type', get_default_error_type(e))


def map_detail(e, **kwargs):
    detail = kwargs.pop('detail', None)
    message = kwargs.pop('message', None)
    code = kwargs.pop('code', None)

    assert detail or message, \
        "Either the detail or the message must be provided."
    assert code or detail, \
        "Either the deatil or the code must be provided."

    return {**{
        'message': message or str(detail),
        'code': code or getattr(detail, 'code'),
        'error_type': get_error_type(e)
    }, **kwargs}


def map_details(e, **kwargs):
    # Allow the details to be explicitly provided in the case that the
    # details are nested on the original exception.
    details = kwargs.pop('details', getattr(e, 'detail'))
    mapped = []
    if isinstance(details, dict):
        for k, v in details.items():
            mapped += map_details(e, details=v, field=k)
    elif isinstance(details, list):
        for detail_i in details:
            if isinstance(detail_i, (list, dict)):
                mapped += map_details(e, details=detail_i, **kwargs)
            else:
                mapped += [map_detail(e, detail=detail_i, **kwargs)]
    else:
        mapped += [map_detail(e, detail=details, **kwargs)]
    return mapped


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
        occurred during form level field validation in a serializer),
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

        (2) bad_request [400] Response
            General errors that do not fall under the field, form or billing
            error types.

        (3) field [400] Response
            Validation errors that are related to failed validation of specific
            fields in the request data.

        (4) form [400] Response
            Validation errors that are related to request data validation that
            does not pertain to a specific field in the request data.

        (5) auth [401] Response
            Validation errors related to proper authentication of a user.  These
            occur when attempting to access a protected resource without being
            authenticated or when the JWT authentication token is being
            validated. In both cases, the Front End identifies when this type
            of error is included in the response and will forcefully log out
            the user.

        (6) billing [400] Response
            Billing related errors that occur when a user is attempting to
            change, update or create subscriptions in Stripe.

        (7) permission [403] Response
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
                `happybudget.app.authentication.exceptions.AuthenticationError`.

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
                >>>     products: ["happybudget_standard"]
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
    # In case a Django ValidationError is raised outside of a serializer's
    # validation methods (as might happen if we don't know the validation error
    # until we send a request to a third party API), convert to a DRF
    # ValidationError.
    if isinstance(exc, DjangoValidationError):
        exc = exceptions.ValidationError(detail=as_serializer_error(exc))

    # If the exception is not an instance of exceptions.APIException, allow
    # the original django-rest-framework exception handler to handle the
    # exception.
    if not isinstance(exc, (exceptions.APIException, Http404)):
        return views.exception_handler(exc, context)

    additional_data = {}
    default_error_type = get_default_error_type(exc)

    # If the error type cannot be determined, we cannot use our own error
    # handling protocols as the API consumer will expect that error type to
    # be defined.
    error_type = getattr(exc, 'error_type', default_error_type)
    if error_type is None:
        logger.warning(
            "Could not determine default error type for exception "
            f"{exc.__class__.__name__}."
        )
        return views.exception_handler(exc, context)

    # If the exception class is initialized or marked as `hard_raise`, then we
    # want to raise the exception without rendering the response.
    hard_raise = getattr(exc, '__hard_raise__', False)
    if hard_raise:
        raise exc

    # By default, Django REST Framework will catch Http404 and return a response
    # { "detail": "Not found." } and will catch exceptions.MethodNotAllowed
    # and return a response { "detail": "Method not allowed." }.
    if isinstance(exc, Http404):
        message = str(exc) or "The requested resource could not be found."
        logger.warning("API encountered a 404 error", extra={
            'error_type': error_type,
            'code': 'not_found'
        })
        return Response(
            {'errors': [map_detail(exc, message=message, code='not_found')]},
            status=status.HTTP_404_NOT_FOUND
        )
    elif isinstance(exc, exceptions.MethodNotAllowed):
        message = str(exc) or "This method is not allowed."
        logger.error("API encountered a 405 error", extra={
            'error_type': 'http',
            'code': 'method_not_allowed'
        })
        return Response(
            {'errors': [map_detail(
                exc, message=message, code='method_not_allowed')]},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    elif isinstance(exc, (
        AuthenticationFailed,
        exceptions.AuthenticationFailed,
        exceptions.NotAuthenticated,
        exceptions.PermissionDenied
    )):
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
                additional_data['user_id'] = user_id

        # There are cases where we need to include information about the products
        # that a user needs to be subscribed to in order to perform a certain
        # action.
        if isinstance(exc, ProductPermissionError):
            additional_data.update(
                products=getattr(exc, 'products'),
                permission_id=getattr(exc, 'permission_id')
            )

    response_data = {'errors': map_details(exc, **additional_data)}

    # Allow the exception to include extra data that will be attributed to the
    # response at the top level, not individual errors.
    if isinstance(getattr(exc, 'extra', None), collections.abc.Mapping):
        response_data.update(exc.extra)

    logger.info("API Error", extra=response_data)

    return Response(response_data, status=exc.status_code)
