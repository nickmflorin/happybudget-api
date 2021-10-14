from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from rest_framework_simplejwt import serializers
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings

from greenbudget.app.authentication.exceptions import (
    EmailNotVerified, AccountDisabledError)

from .exceptions import (
    InvalidToken, ExpiredToken, TokenExpiredError, TokenInvalidError)
from .tokens import (
    GreenbudgetSlidingToken,
    GreenbudgetEmailVerificationSlidingToken
)


def parse_token_from_request(request):
    return request.COOKIES.get(settings.JWT_TOKEN_COOKIE_NAME)


def verify_token(token, token_cls=None):
    token_cls = token_cls or GreenbudgetSlidingToken
    token = token or ''
    try:
        token_obj = token_cls(token, verify=False)
    except TokenError as e:
        raise TokenInvalidError(*e.args) from e
    try:
        token_obj.check_exp(api_settings.SLIDING_TOKEN_REFRESH_EXP_CLAIM)
    except TokenError as e:
        raise TokenExpiredError(*e.args) from e
    token_obj.set_exp()
    try:
        token_obj.verify()
    except TokenError as e:
        raise TokenInvalidError(*e.args) from e
    return token_obj


def get_user_from_token(token, token_cls=None):
    token_cls = token_cls or GreenbudgetSlidingToken
    assert token_cls in (
        GreenbudgetSlidingToken,
        GreenbudgetEmailVerificationSlidingToken
    )
    if token is not None:
        token_obj = verify_token(token, token_cls=token_cls)
        user_id = token_obj.get(api_settings.USER_ID_CLAIM)
        # This is an edge case where an old JWT might be stashed in the browser
        # but the user may have been deleted.
        try:
            return get_user_model().objects.get(pk=user_id)
        except get_user_model().DoesNotExist:
            return AnonymousUser()
    return AnonymousUser()


class TokenRefreshSerializer(serializers.TokenRefreshSlidingSerializer):
    token_cls = GreenbudgetSlidingToken

    def validate(self, attrs):
        try:
            return get_user_from_token(attrs['token'], token_cls=self.token_cls)
        except TokenExpiredError as e:
            raise ExpiredToken(*e.args) from e
        except TokenError as e:
            raise InvalidToken(*e.args) from e


class EmailTokenRefreshSerializer(TokenRefreshSerializer):
    token_cls = GreenbudgetEmailVerificationSlidingToken

    def validate(self, attrs):
        user = super().validate(attrs)
        if not user.is_active:
            raise AccountDisabledError()
        return user


class UserTokenRefreshSerializer(EmailTokenRefreshSerializer):
    token_cls = GreenbudgetSlidingToken

    def validate(self, attrs):
        user = super().validate(attrs)
        if not user.is_verified:
            raise EmailNotVerified()
        return user
