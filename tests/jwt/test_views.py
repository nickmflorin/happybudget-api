from datetime import datetime
from http.cookies import SimpleCookie
import pytest

from greenbudget.app.jwt.tokens import GreenbudgetSlidingToken


def test_moving_date(freezer):
    now = datetime.now()
    freezer.move_to('2017-05-20')
    later = datetime.now()
    assert now != later


@pytest.mark.freeze_time('2020-01-01')
def test_validate_token(api_client, settings, user):
    api_client.force_login(user)

    token = GreenbudgetSlidingToken.for_user(user)
    api_client.cookies = SimpleCookie({
        settings.JWT_TOKEN_COOKIE_NAME: str(token),
    })
    response = api_client.post("/v1/jwt/validate/")
    assert response.status_code == 201
    assert 'greenbudgetjwt' in response.cookies

    assert response.json() == {}


@pytest.mark.freeze_time('2020-01-01')
def test_validate_token_missing_token(api_client, db):
    response = api_client.post("/v1/jwt/validate/")
    assert response.status_code == 403


@pytest.mark.freeze_time('2020-01-01')
def test_validate_token_invalid_token(api_client, settings, db):
    api_client.cookies = SimpleCookie({
        settings.JWT_TOKEN_COOKIE_NAME: "invalid-token"
    })
    response = api_client.post("/v1/jwt/validate/")
    assert response.status_code == 403
