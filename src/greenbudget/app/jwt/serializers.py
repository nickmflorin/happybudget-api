from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from rest_framework_simplejwt import serializers
from rest_framework_simplejwt.settings import api_settings

from greenbudget.app.authentication.backends import check_user_permissions

from .exceptions import (
    InvalidToken, ExpiredToken, TokenExpiredError, TokenInvalidError,
    TokenCorruptedError, TokenError, BaseTokenError)
from .tokens import (
    GreenbudgetSlidingToken,
    GreenbudgetEmailVerificationSlidingToken
)


def parse_token_from_request(request):
    return request.COOKIES.get(settings.JWT_TOKEN_COOKIE_NAME)


def verify_token(token, token_cls=None):
    token_cls = token_cls or GreenbudgetSlidingToken
    assert token is not None and isinstance(token, str), \
        "The token must be a valid string."
    try:
        token_obj = token_cls(token, verify=False)
    except BaseTokenError as e:
        raise TokenInvalidError() from e

    # We need to parse and verify the user ID associated with the token in order
    # to include that information in the TokenExpiredError exception which
    # funnels to the Front End and is needed for email verification purposes.
    user_id = token_obj.get(api_settings.USER_ID_CLAIM)
    try:
        user = get_user_model().objects.get(pk=user_id)
    except get_user_model().DoesNotExist:
        # This is an edge case where an old JWT might be stashed in the browser
        # but the user may have been deleted.
        raise TokenCorruptedError()
    try:
        token_obj.check_exp(api_settings.SLIDING_TOKEN_REFRESH_EXP_CLAIM)
    except BaseTokenError as e:
        raise TokenExpiredError(user_id=user_id) from e
    token_obj.set_exp()
    try:
        token_obj.verify()
    except BaseTokenError as e:
        raise TokenInvalidError(user_id=user_id) from e
    return user, token_obj


def get_user_from_token(token, token_cls=None, strict=False):
    if token is not None:
        return verify_token(token, token_cls=token_cls)
    if strict:
        raise TokenInvalidError()
    return AnonymousUser(), None


class TokenRefreshSerializer(serializers.TokenRefreshSlidingSerializer):

    def __init__(self, *args, **kwargs):
        default_token_cls = getattr(self, 'token_cls', GreenbudgetSlidingToken)
        self.token_cls = kwargs.pop('token_cls', default_token_cls)

        self.force_logout = kwargs.pop('force_logout', None)

        default_exclude_permissions = getattr(self, 'exclude_permissions', [])
        self.exclude_permissions = kwargs.pop(
            'exclude_permissions', default_exclude_permissions)
        super().__init__(*args, **kwargs)

    def validate(self, attrs):
        try:
            user, token_obj = get_user_from_token(
                token=attrs['token'],
                token_cls=self.token_cls,
                strict=True
            )
        except TokenExpiredError as e:
            raise ExpiredToken(
                *e.args,
                user_id=getattr(e, 'user_id', None),
                force_logout=self.force_logout
            ) from e
        except TokenError as e:
            raise InvalidToken(
                *e.args,
                user_id=getattr(e, 'user_id', None),
                force_logout=self.force_logout
            ) from e
        check_user_permissions(
            user=user,
            exclude_permissions=self.exclude_permissions,
            raise_exception=True,
            force_logout=self.force_logout
        )
        return user, token_obj


class EmailTokenRefreshSerializer(TokenRefreshSerializer):
    token_cls = GreenbudgetEmailVerificationSlidingToken
    exclude_permissions = ['verified']
