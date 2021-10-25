import collections
import logging
import requests

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.exceptions import TokenError

from greenbudget.lib.utils.urls import add_query_params_to_url

from .exceptions import (
    BaseTokenError, TokenInvalidError, TokenCorruptedError, TokenExpiredError,
    InvalidSocialToken, InvalidSocialProvider, InvalidToken, ExpiredToken)
from .tokens import AuthToken


logger = logging.getLogger('greenbudget')


SocialUser = collections.namedtuple(
    'SocialUser', ['first_name', 'last_name', 'email'])


def validate_password(password):
    for validator in settings.PASSWORD_VALIDATORS:
        validator.validate(password)


def parse_token_from_request(request):
    return request.COOKIES.get(settings.JWT_TOKEN_COOKIE_NAME)


def parse_user_id_from_token(token_obj):
    return token_obj.get(api_settings.USER_ID_CLAIM)


def parse_token(token, token_cls=None, api_context=False, force_logout=False):
    # If the function is being run in the API context, perform the logic and
    # convert any raised exceptions to REST Exceptions that will properly render
    # via the API.
    if api_context:
        try:
            return parse_token(token, token_cls=None)
        except TokenCorruptedError as e:
            logger.info("The provided token is corrupted.")
            raise InvalidToken(
                *e.args,
                user_id=getattr(e, 'user_id', None),
                force_logout=force_logout
            ) from e
        except TokenExpiredError as e:
            logger.info("The provided token has expired.")
            raise ExpiredToken(
                *e.args,
                user_id=getattr(e, 'user_id', None),
                force_logout=force_logout
            ) from e
        except TokenError as e:
            logger.info("The provided token is invalid.")
            raise InvalidToken(
                *e.args,
                user_id=getattr(e, 'user_id', None),
                force_logout=force_logout
            ) from e

    if token is None:
        return AnonymousUser(), None

    token_cls = token_cls or AuthToken
    assert token is not None and isinstance(token, str), \
        "The token must be a valid string."
    try:
        token_obj = token_cls(token, verify=False)
    except BaseTokenError as e:
        raise TokenInvalidError() from e

    # We need to parse and verify the user ID associated with the token in order
    # to include that information in the TokenExpiredError exception which
    # funnels to the Front End and is needed for email verification purposes.
    user_id = parse_user_id_from_token(token_obj)
    try:
        user = get_user_model().objects.get(pk=user_id)
    except get_user_model().DoesNotExist:
        # This is an edge case where an old JWT might be stashed in the browser
        # but the user may have been deleted.
        raise TokenCorruptedError()

    exp_claim = api_settings.SLIDING_TOKEN_REFRESH_EXP_CLAIM \
        if token_cls is AuthToken else "exp"

    try:
        token_obj.check_exp(exp_claim)
    except BaseTokenError as e:
        raise TokenExpiredError(user_id=user_id) from e
    token_obj.set_exp()
    try:
        token_obj.verify()
    except BaseTokenError as e:
        raise TokenInvalidError(user_id=user_id) from e
    return user, token_obj


def get_google_user_from_token(token):
    url = add_query_params_to_url(settings.GOOGLE_OAUTH_API_URL, id_token=token)
    try:
        response = requests.get(url)
    except requests.RequestException as e:
        logger.error("Network Error Validating Google Token: %s" % e)
        raise InvalidSocialToken()
    else:
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.error("HTTP Error Validating Google Token: %s" % e)
            raise InvalidSocialToken()
        else:
            data = response.json()
            return SocialUser(
                first_name=data['given_name'],
                last_name=data['family_name'],
                email=data['email']
            )


def get_user_from_social_token(token, provider):
    if provider != "google":
        raise InvalidSocialProvider()
    return get_google_user_from_token(token)
