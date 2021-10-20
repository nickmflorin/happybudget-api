from django.conf import settings

from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import (
    Token as BaseToken,
    SlidingToken as BaseSlidingToken,
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
    the token lifetimes when the settings change (because the lifetimes
    are defined as static attributes, not defined dynamically in the __init__
    method).
    """

    def __init__(self, token=None, verify=True, lifetime=None):
        self.lifetime = lifetime or getattr(self, 'lifetime', None)
        super().__init__(token=token, verify=verify)


class SlidingToken(BlacklistMixin, Token):
    token_type = BaseSlidingToken.token_type

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


class AccessToken(Token):
    token_type = BaseAccessToken.token_type

    def __init__(self, *args, **kwargs):
        kwargs['lifetime'] = settings.ACCESS_TOKEN_LIFETIME
        super().__init__(*args, **kwargs)
