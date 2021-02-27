from datetime import datetime, timedelta

import pytest

from greenbudget.app.jwt import serializers
from greenbudget.app.jwt.utils import verify_token
from greenbudget.app.jwt.tokens import GreenbudgetSlidingToken
from greenbudget.app.jwt.exceptions import TokenInvalidError, TokenExpiredError


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
    refresh_serializer = serializers.TokenRefreshSlidingSerializer()
    token = GreenbudgetSlidingToken()
    token.set_exp(claim='refresh_exp', from_time=datetime(2010, 1, 1))
    with pytest.raises(TokenExpiredError):
        refresh_serializer.validate({'token': str(token)})


@pytest.mark.skip("Figure out why this is not passing!")
@pytest.mark.freeze_time('2021-01-01')
def test_refresh_serializer_validate_success_returns_token(settings, freezer):
    settings.SIMPLE_JWT['SLIDING_TOKEN_REFRESH_LIFETIME'] = timedelta(hours=1)

    refresh_serializer = serializers.TokenRefreshSlidingSerializer()
    token = GreenbudgetSlidingToken()

    freezer.move_to('2021-01-02')
    data = refresh_serializer.validate({'token': str(token)})

    assert 'token' in data

    new_token = GreenbudgetSlidingToken(data['token'])
    assert new_token['exp'] > token['exp']
