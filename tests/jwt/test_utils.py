from datetime import datetime
from unittest import mock

import pytest

from django.contrib.auth.models import AnonymousUser

from greenbudget.app.jwt.exceptions import TokenExpiredError
from greenbudget.app.jwt.tokens import GreenbudgetSlidingToken
from greenbudget.app.jwt.utils import get_user_from_token
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
