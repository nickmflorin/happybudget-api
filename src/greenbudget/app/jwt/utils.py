from typing import Optional, Union

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, AbstractUser

from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.exceptions import TokenError

from .exceptions import TokenExpiredError, TokenInvalidError
from .tokens import GreenbudgetSlidingToken


def verify_token(token):
    token = token or ''
    try:
        token_obj = GreenbudgetSlidingToken(token, verify=False)
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


def get_user_from_token(token: Optional[str]) -> Union[
        AnonymousUser, AbstractUser]:
    from .serializers import TokenRefreshSlidingSerializer

    if token is not None:
        refresh_serializer = TokenRefreshSlidingSerializer()
        data = refresh_serializer.validate({'token': token})
        token_obj = verify_token(data['token'])
        user_id = token_obj.get(api_settings.USER_ID_CLAIM)
        return get_user_model().objects.get(pk=user_id)
    return AnonymousUser()
