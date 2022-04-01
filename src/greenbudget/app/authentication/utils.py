import logging

from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework_simplejwt.settings import api_settings

from greenbudget.lib.utils import empty
from greenbudget.app.user.contrib import AnonymousUser

from .exceptions import BaseTokenError, InvalidToken, ExpiredToken
from .models import AnonymousPublicToken, PublicToken
from .tokens import AuthToken


logger = logging.getLogger('greenbudget')


def validate_password(password):
    for validator in settings.PASSWORD_VALIDATORS:
        validator.validate(password)


def parse_token_from_request(request):
    return request.COOKIES.get(settings.JWT_TOKEN_COOKIE_NAME)


def parse_public_token_from_request(request):
    return request.META.get(settings.PUBLIC_TOKEN_HEADER)


def parse_user_id_from_token(token_obj):
    return token_obj.get(api_settings.USER_ID_CLAIM)


def parse_public_token(token=empty, request=None, instance=None, public=False):
    assert token is not empty or request is not None, \
        "Either the request or token must be provided."
    if token is empty:
        token = parse_public_token_from_request(request)
        return parse_public_token(token=token, instance=instance, public=public)

    if token is None:
        return AnonymousPublicToken()

    kwargs = {'public_id': str(token)} if public else {'private_id': str(token)}
    try:
        public_token = PublicToken.objects.get(**kwargs)
    except PublicToken.DoesNotExist as e:
        raise InvalidToken() from e
    else:
        if instance is not None and public_token.instance != instance:
            raise InvalidToken()
        elif public_token.is_expired:
            raise ExpiredToken()
        return public_token


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
    except BaseTokenError as e:
        raise InvalidToken() from e

    # We need to parse and verify the user ID associated with the token in order
    # to include that information in the TokenExpiredError exception which
    # funnels to the Front End and is needed for email verification purposes.
    user_id = parse_user_id_from_token(token_obj)
    try:
        user = get_user_model().objects.get(pk=user_id)
    except get_user_model().DoesNotExist as e:
        # This is an edge case where an old JWT might be stashed in the browser
        # but the user may have been deleted.
        raise InvalidToken() from e

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
