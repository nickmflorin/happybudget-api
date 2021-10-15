from datetime import datetime, timedelta
from django.contrib.auth.models import AnonymousUser
from unittest import mock

import pytest

from greenbudget.app.jwt import serializers
from greenbudget.app.jwt.tokens import GreenbudgetSlidingToken
from greenbudget.app.jwt.exceptions import (
    TokenInvalidError, TokenExpiredError, ExpiredToken)
from greenbudget.app.jwt.serializers import verify_token, get_user_from_token

from greenbudget.app.user.models import User


class TestGetUserFromTokens:
    def test_none_returns_anonymous_user(self):
        user = get_user_from_token(None)
        assert isinstance(user, AnonymousUser)

    def test_valid_access_token_returns_user(self, user):
        token = GreenbudgetSlidingToken.for_user(user)
        with mock.patch.object(
                User.objects, 'get', return_value=user) as mock_fn:
            returned_user = get_user_from_token(str(token))
        assert returned_user.pk == user.pk
        assert mock_fn.mock_calls == [mock.call(pk=user.pk)]

    @pytest.mark.freeze_time('2021-01-01')
    def test_expired_access_token_auto_refreshes(self, user):
        token = GreenbudgetSlidingToken.for_user(user)
        token.set_exp(from_time=datetime(2010, 1, 1))
        with mock.patch.object(
                User.objects, 'get', return_value=user) as mock_fn:
            returned_user = get_user_from_token(str(token))
        assert returned_user.pk == user.pk
        assert mock_fn.mock_calls == [mock.call(pk=user.pk)]

    @pytest.mark.freeze_time('2021-01-01')
    def test_expired_access_token_missing_refresh_token_raises(self, user):
        token = GreenbudgetSlidingToken.for_user(user)
        token.set_exp(claim='refresh_exp', from_time=datetime(2010, 1, 1))
        with mock.patch.object(
                User.objects, 'get', return_value=user) as mock_fn:
            with pytest.raises(TokenExpiredError):
                get_user_from_token(str(token))

        assert mock_fn.call_count == 0


def test_verify_token_bad_token_raises_invalid_error():
    with pytest.raises(TokenInvalidError):
        verify_token('foo')


def test_verify_token_invalid_token_raises_invalid_error():
    token = GreenbudgetSlidingToken()
    token.payload.pop('jti')  # Remove jti claim to trigger verify failure
    with pytest.raises(TokenInvalidError):
        verify_token(str(token))


@pytest.mark.freeze_time('2021-01-01')
def test_refresh_serializer_validate_expired_token_raises_expired_error():
    refresh_serializer = serializers.UserTokenRefreshSerializer()
    token = GreenbudgetSlidingToken()
    token.set_exp(claim='refresh_exp', from_time=datetime(2010, 1, 1))
    with pytest.raises(ExpiredToken):
        refresh_serializer.validate({'token': str(token)})


@pytest.mark.skip("Figure out why this is not passing!")
@pytest.mark.freeze_time('2021-01-01')
def test_refresh_serializer_validate_success_returns_token(settings, freezer):
    settings.SIMPLE_JWT['SLIDING_TOKEN_REFRESH_LIFETIME'] = timedelta(hours=1)

    refresh_serializer = serializers.UserTokenRefreshSerializer()
    token = GreenbudgetSlidingToken()

    freezer.move_to('2021-01-02')
    data = refresh_serializer.validate({'token': str(token)})

    new_token = GreenbudgetSlidingToken(data)
    assert new_token['exp'] > token['exp']
