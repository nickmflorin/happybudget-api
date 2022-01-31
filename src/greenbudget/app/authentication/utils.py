from .tokens import AuthToken
from .models import ShareToken
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from rest_framework import permissions
from rest_framework_simplejwt.settings import api_settings

from greenbudget.lib.utils import empty

from .exceptions import (
    BaseTokenError, InvalidToken, ExpiredToken, NotAuthenticatedError)
from .models import AnonymousShareToken


logger = logging.getLogger('greenbudget')


def request_is_write_method(request):
    return not request_is_safe_method(request)


def request_is_safe_method(request):
    return request.method in permissions.SAFE_METHODS


def request_is_admin(request):
    return '/admin/' in request.path


def user_can_authenticate(user, raise_exception=True, permissions=None):
    from greenbudget.app.permissions import check_user_permissions
    try:
        check_user_permissions(user, permissions=permissions)
    except NotAuthenticatedError as e:
        if raise_exception:
            raise e
        return None
    return user


def validate_password(password):
    for validator in settings.PASSWORD_VALIDATORS:
        validator.validate(password)


def parse_token_from_request(request):
    return request.COOKIES.get(settings.JWT_TOKEN_COOKIE_NAME)


def parse_share_token_from_request(request):
    return request.headers.get(settings.SHARE_TOKEN_HEADER)


def parse_user_id_from_token(token_obj):
    return token_obj.get(api_settings.USER_ID_CLAIM)


def parse_share_token(token=empty, request=None, instance=None, public=False):
    assert token is not empty or request is not None, \
        "Either the request or token must be provided."
    if token is empty:
        token = parse_share_token_from_request(request)
        return parse_share_token(token=token, instance=instance, public=public)

    if token is None:
        return AnonymousShareToken()

    kwargs = {'public_id': str(token)} if public else {'private_id': str(token)}
    try:
        share_token = ShareToken.objects.get(**kwargs)
    except ShareToken.DoesNotExist:
        raise InvalidToken()
    else:
        if instance is not None and share_token.instance != instance:
            raise InvalidToken()
        elif share_token.is_expired:
            raise ExpiredToken()
        return share_token


def parse_token(token=empty, request=None, token_cls=None):
    assert token is not empty or request is not None, \
        "Either the request or token must be provided."
    if token is empty:
        token = parse_token_from_request(request)
        return parse_token(token=token, token_cls=token_cls)

    assert token is None or isinstance(token, str), \
        "The token must be a valid string or None."

    if token is None:
        return AnonymousUser(), None

    token_cls = token_cls or AuthToken
    try:
        token_obj = token_cls(token, verify=False)
    except BaseTokenError:
        raise InvalidToken()

    # We need to parse and verify the user ID associated with the token in order
    # to include that information in the TokenExpiredError exception which
    # funnels to the Front End and is needed for email verification purposes.
    user_id = parse_user_id_from_token(token_obj)
    try:
        user = get_user_model().objects.get(pk=user_id)
    except get_user_model().DoesNotExist:
        # This is an edge case where an old JWT might be stashed in the browser
        # but the user may have been deleted.
        raise InvalidToken()

    exp_claim = api_settings.SLIDING_TOKEN_REFRESH_EXP_CLAIM \
        if token_cls is AuthToken else "exp"

    try:
        token_obj.check_exp(exp_claim)
    except BaseTokenError as e:
        logger.info("The provided token has expired.")
        raise ExpiredToken(user_id=user_id) from e

    token_obj.set_exp()
    try:
        token_obj.verify()
    except BaseTokenError as e:
        logger.info("The provided token is invalid.")
        raise InvalidToken(user_id=user_id) from e

    return user, token_obj
