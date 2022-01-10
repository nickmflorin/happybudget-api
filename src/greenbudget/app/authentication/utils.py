import collections
import logging
import requests

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from rest_framework_simplejwt.settings import api_settings

from greenbudget.lib.utils.urls import add_query_params_to_url

from .exceptions import (
    BaseTokenError, InvalidSocialToken, InvalidSocialProvider, InvalidToken,
    ExpiredToken, NotAuthenticatedError)
from .permissions import check_user_permissions
from .tokens import AuthToken


logger = logging.getLogger('greenbudget')


SocialUser = collections.namedtuple(
    'SocialUser', ['first_name', 'last_name', 'email'])


def user_can_authenticate(user, raise_exception=True, permissions=None):
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


def parse_user_id_from_token(token_obj):
    return token_obj.get(api_settings.USER_ID_CLAIM)


def parse_token(token, token_cls=None):
    if token is None:
        return AnonymousUser(), None

    token_cls = token_cls or AuthToken
    assert token is not None and isinstance(token, str), \
        "The token must be a valid string."
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
