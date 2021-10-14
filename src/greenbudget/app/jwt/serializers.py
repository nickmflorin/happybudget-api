from rest_framework_simplejwt import serializers
from rest_framework_simplejwt.exceptions import TokenError

from greenbudget.app.authentication.exceptions import (
    EmailNotVerified, AccountDisabledError)

from .exceptions import InvalidToken, ExpiredToken, TokenExpiredError
from .utils import verify_token, get_user_from_token


class TokenRefreshSlidingSerializer(serializers.TokenRefreshSlidingSerializer):
    def validate(self, attrs):
        return verify_token(attrs['token'])


class UserTokenSlidingSerializer(serializers.TokenRefreshSlidingSerializer):
    def validate(self, attrs, require_verification=True):
        try:
            user = get_user_from_token(attrs['token'])
        except TokenExpiredError as e:
            raise ExpiredToken(*e.args) from e
        except TokenError as e:
            raise InvalidToken(*e.args) from e
        if not user.is_active:
            raise AccountDisabledError()
        elif not user.is_verified and require_verification:
            raise EmailNotVerified()
        return user
