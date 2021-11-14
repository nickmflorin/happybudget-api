from datetime import datetime
from django.contrib.auth.models import AnonymousUser
from unittest import mock

import pytest

from greenbudget.app.authentication.tokens import (
    AuthToken, AccessToken)
from greenbudget.app.authentication.exceptions import (
    TokenInvalidError, TokenExpiredError)
from greenbudget.app.authentication.utils import (
    verify_token, get_user_from_token)

from greenbudget.app.user.models import User


class TestGetUserFromAuthTokens:
    def test_none_returns_anonymous_user(self):
        user, token_obj = get_user_from_token(None)
        assert isinstance(user, AnonymousUser)
        assert token_obj is None

    def test_valid_access_token_returns_user(self, user):
        token = AuthToken.for_user(user)
        with mock.patch.object(
                User.objects, 'get', return_value=user) as mock_fn:
            returned_user, _ = get_user_from_token(str(token))
        assert returned_user.pk == user.pk
        assert mock_fn.mock_calls == [mock.call(pk=user.pk)]

    @pytest.mark.freeze_time('2021-01-01')
    def test_expired_access_token_auto_refreshes(self, user):
        token = AuthToken.for_user(user)
        token.set_exp(from_time=datetime(2010, 1, 1))
        with mock.patch.object(
                User.objects, 'get', return_value=user) as mock_fn:
            returned_user, _ = get_user_from_token(str(token))
        assert returned_user.pk == user.pk
        assert mock_fn.mock_calls == [mock.call(pk=user.pk)]

    @pytest.mark.freeze_time('2021-01-01')
    def test_expired_access_token_missing_refresh_token_raises(self, user):
        token = AuthToken.for_user(user)
        token.set_exp(claim='refresh_exp', from_time=datetime(2010, 1, 1))
        with mock.patch.object(
                User.objects, 'get', return_value=user) as mock_fn:
            with pytest.raises(TokenExpiredError):
                get_user_from_token(str(token))

        assert mock_fn.call_count == 1


class TestGetUserFromAccessTokens:

    def test_valid_access_token_returns_user(self, user):
        token = AccessToken.for_user(user)
        with mock.patch.object(
                User.objects, 'get', return_value=user) as mock_fn:
            returned_user, _ = get_user_from_token(
                str(token), token_cls=AccessToken)
        assert returned_user.pk == user.pk
        assert mock_fn.mock_calls == [mock.call(pk=user.pk)]

    @pytest.mark.freeze_time('2021-01-01')
    def test_expired_access_token_missing_refresh_token_raises(self, user):
        token = AccessToken.for_user(user)
        token.set_exp(claim='exp', from_time=datetime(2010, 1, 1))
        with mock.patch.object(
                User.objects, 'get', return_value=user) as mock_fn:
            with pytest.raises(TokenExpiredError):
                get_user_from_token(str(token), token_cls=AccessToken)

        assert mock_fn.call_count == 1


def test_verify_token_bad_token_raises_invalid_error():
    with pytest.raises(TokenInvalidError):
        verify_token('foo')


def test_auth_token_invalid_token_raises_invalid_error(user):
    token = AuthToken.for_user(user)
    token.payload.pop('jti')  # Remove jti claim to trigger verify failure
    with pytest.raises(TokenInvalidError):
        verify_token(str(token))


def test_access_token_invalid_token_raises_invalid_error(user):
    token = AccessToken.for_user(user)
    token.payload.pop('jti')  # Remove jti claim to trigger verify failure
    with pytest.raises(TokenInvalidError):
        verify_token(str(token), token_cls=AccessToken)
