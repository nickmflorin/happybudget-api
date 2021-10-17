from datetime import datetime, timedelta
from django.conf import settings
from django.test.utils import override_settings

import pytest

from greenbudget.app.authentication.tokens import (
    AuthSlidingToken, EmailVerificationSlidingToken)
from greenbudget.app.authentication.exceptions import ExpiredToken
from greenbudget.app.authentication.serializers import (
    TokenRefreshSerializer, EmailTokenRefreshSerializer)


@pytest.mark.freeze_time('2021-01-01')
def test_auth_serializer_validate_expired_token_raises_expired_error(user):
    refresh_serializer = TokenRefreshSerializer()
    token = AuthSlidingToken.for_user(user)
    token.set_exp(claim='refresh_exp', from_time=datetime(2010, 1, 1))
    with pytest.raises(ExpiredToken):
        refresh_serializer.validate({'token': str(token)})


@pytest.mark.freeze_time('2021-01-01')
def test_email_serializer_validate_expired_token_raises_expired_error(user):
    refresh_serializer = EmailTokenRefreshSerializer()
    token = EmailVerificationSlidingToken.for_user(user)
    token.set_exp(claim='refresh_exp', from_time=datetime(2010, 1, 1))
    with pytest.raises(ExpiredToken):
        refresh_serializer.validate({'token': str(token)})


@override_settings(SIMPLE_JWT={
    **settings.SIMPLE_JWT,
    **{"SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=30)}
})
@pytest.mark.freeze_time('2021-01-01')
def test_auth_serializer_validate_success_returns_token(user, freezer):
    refresh_serializer = TokenRefreshSerializer()
    token = AuthSlidingToken.for_user(user)

    freezer.move_to('2021-01-02')
    user, token_obj = refresh_serializer.validate({'token': str(token)})
    new_token = AuthSlidingToken(str(token_obj))
    assert new_token['exp'] > token['exp']


@override_settings(EMAIL_VERIFICATION_JWT_EXPIRY=timedelta(days=30))
@pytest.mark.freeze_time('2021-01-01')
def test_email_serializer_validate_success_returns_token(user, freezer):
    refresh_serializer = EmailTokenRefreshSerializer()
    token = EmailVerificationSlidingToken.for_user(user)

    freezer.move_to('2021-01-02')
    user, token_obj = refresh_serializer.validate({'token': str(token)})
    new_token = EmailVerificationSlidingToken(str(token_obj))
    assert new_token['exp'] > token['exp']
