from django.conf import settings

from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import (
    Token as BaseToken,
    SlidingToken,
    AccessToken as BaseAccessToken,
    BlacklistMixin
)


class Token(BaseToken):
    """
    An extension of :obj:`rest_framework_simplejwt.tokens.Token` that sets
    the lifetime values of the token dynamically based on Django's settings,
    not rest_framework_simplejwt`s settings.

    This is required for tests and other situations where the settings
    configuration for these tokens might change, because the
    rest_framework_simplejwt package does not do an adequate job adjusting
    the token lifetimes after there is a change to Django's settings.

    This is because the token lifetmies are defined as static class attributes,
    not defined dynamically in the __init__ method, so overriding the settings
    will not cause the tokens to use a different lifetime.
    """
    def __init__(self, token=None, verify=True, lifetime=None):
        self.lifetime = lifetime or getattr(self, 'lifetime', None)
        super().__init__(token=token, verify=verify)


class AuthToken(BlacklistMixin, Token):
    """
    Token used for verifying user authentication and identity in the
    application and maintaining their logged in state.  Additionally, the
    token is used for maintaining the billing/subscription status of the
    user.
    """
    token_type = SlidingToken.token_type

    def __init__(self, *args, **kwargs):
        kwargs['lifetime'] = settings.SLIDING_TOKEN_LIFETIME
        super().__init__(*args, **kwargs)
        if self.token is None:
            # Set sliding refresh expiration claim if new token
            self.set_exp(
                api_settings.SLIDING_TOKEN_REFRESH_EXP_CLAIM,
                from_time=self.current_time,
                lifetime=settings.SLIDING_TOKEN_REFRESH_LIFETIME,
            )

    @classmethod
    def for_user(cls, user):
        token = super().for_user(user)
        if settings.BILLING_ENABLED:
            token.payload.update(
                billing_status=user.billing_status,
                product_id=user.product_id
            )
        return token


class AccessToken(Token):
    """
    Token used for other user sensitive actions such as password reset and
    email verification.
    """
    token_type = BaseAccessToken.token_type

    def __init__(self, *args, **kwargs):
        kwargs['lifetime'] = settings.ACCESS_TOKEN_LIFETIME
        super().__init__(*args, **kwargs)
