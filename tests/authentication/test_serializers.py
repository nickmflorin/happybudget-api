from datetime import datetime, timedelta
from django.test.utils import override_settings

import pytest

from greenbudget.app.authentication.tokens import SlidingToken, AccessToken
from greenbudget.app.authentication.exceptions import ExpiredToken
from greenbudget.app.authentication.serializers import (
    AuthTokenSerializer, EmailTokenSerializer)


@pytest.mark.freeze_time('2021-01-01')
@pytest.mark.parametrize("serializer_cls,token_cls,claim", [
    (AuthTokenSerializer, SlidingToken, "refresh_exp"),
    (AuthTokenSerializer, AccessToken, "exp"),
    (EmailTokenSerializer, AccessToken, "exp"),
])
def test_serializer_validate_expired_token_raises_expired_error(user,
        serializer_cls, token_cls, claim):
    serializer = serializer_cls()
    token = token_cls.for_user(user)
    token.set_exp(claim=claim, from_time=datetime(2010, 1, 1))
    with pytest.raises(ExpiredToken):
        serializer.validate({'token': str(token)})


@override_settings(SLIDING_TOKEN_REFRESH_LIFETIME=timedelta(days=30))
@pytest.mark.freeze_time('2021-01-01')
def test_sliding_serializer_validate_success_returns_token(user, freezer):
    token = SlidingToken.for_user(user)
    refresh_serializer = AuthTokenSerializer()
    freezer.move_to('2021-01-02')
    data = refresh_serializer.validate({'token': str(token)})
    new_token = SlidingToken(str(data["token"]))
    assert new_token["exp"] > token["exp"]


@override_settings(ACCESS_TOKEN_LIFETIME=timedelta(days=30))
@pytest.mark.freeze_time('2021-01-01')
def test_email_token_serializer_create_success_returns_user(unverified_user):
    token = AccessToken.for_user(unverified_user)
    serializer = EmailTokenSerializer(data={'token': str(token)})
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    assert user.is_verified
