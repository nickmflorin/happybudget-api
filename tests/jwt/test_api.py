from http.cookies import SimpleCookie
import pytest

from greenbudget.lib.utils.dateutils import api_datetime_string
from greenbudget.app.jwt.tokens import GreenbudgetSlidingToken


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

    assert response.json() == {
        'user': {
            'id': user.pk,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.full_name,
            'email': user.email,
            'is_active': user.is_active,
            'is_admin': user.is_admin,
            'is_superuser': user.is_superuser,
            'is_staff': user.is_staff,
            'date_joined': api_datetime_string(user.date_joined),
            'updated_at': api_datetime_string(user.updated_at),
            'created_at': api_datetime_string(user.created_at),
            'last_login': '2020-01-01 00:00:00',
            'timezone': str(user.timezone),
            "profile_image": None,
            "is_first_time": False
        }
    }


@pytest.mark.freeze_time('2020-01-01')
def test_force_logout_on_token_removal(api_client, settings, user):
    api_client.force_login(user)

    token = GreenbudgetSlidingToken.for_user(user)
    api_client.cookies = SimpleCookie({
        settings.JWT_TOKEN_COOKIE_NAME: str(token),
    })
    response = api_client.post("/v1/jwt/validate/")
    assert response.status_code == 201
    assert 'greenbudgetjwt' in response.cookies

    api_client.logout()
    response = api_client.get("/v1/budgets/")
    assert response.status_code == 403


def test_validate_token_inactive_user(api_client, settings, user):
    token = GreenbudgetSlidingToken.for_user(user)
    api_client.cookies = SimpleCookie({
        settings.JWT_TOKEN_COOKIE_NAME: str(token),
    })
    user.is_active = False
    user.save()
    response = api_client.post("/v1/jwt/validate/")
    assert response.status_code == 403
    assert response.json() == {
        'user_id': user.pk,
        'errors': [{
            'message': 'Your account is not active, please contact customer care.',  # noqa
            'code': 'account_disabled',
            'error_type': 'auth'
        }]
    }
    assert 'greenbudgetjwt' not in response.cookies


def test_validate_token_inactive_user_logged_in(api_client, settings, user):
    api_client.force_login(user)
    token = GreenbudgetSlidingToken.for_user(user)
    api_client.cookies = SimpleCookie({
        settings.JWT_TOKEN_COOKIE_NAME: str(token),
    })
    user.is_active = False
    user.save()
    response = api_client.post("/v1/jwt/validate/")
    assert response.status_code == 403
    assert response.json() == {
        'user_id': user.pk,
        'force_logout': True,
        'errors': [{
            'message': 'Your account is not active, please contact customer care.',  # noqa
            'code': 'account_disabled',
            'error_type': 'auth'
        }]
    }
    assert response.cookies['greenbudgetjwt'].value == ''


def test_validate_token_unverified_user(api_client, settings, user):
    token = GreenbudgetSlidingToken.for_user(user)
    api_client.cookies = SimpleCookie({
        settings.JWT_TOKEN_COOKIE_NAME: str(token),
    })
    user.is_verified = False
    user.save()
    response = api_client.post("/v1/jwt/validate/")
    assert response.status_code == 403
    assert response.json() == {
        'user_id': user.pk,
        'errors': [{
            'message': 'The email address is not verified.',
            'code': 'email_not_verified',
            'error_type': 'auth'
        }]
    }
    assert 'greenbudgetjwt' not in response.cookies


def test_validate_token_unverified_user_logged_in(api_client, settings, user):
    api_client.force_login(user)
    token = GreenbudgetSlidingToken.for_user(user)
    api_client.cookies = SimpleCookie({
        settings.JWT_TOKEN_COOKIE_NAME: str(token),
    })
    user.is_verified = False
    user.save()
    response = api_client.post("/v1/jwt/validate/")

    assert response.status_code == 403
    assert response.json() == {
        'user_id': user.pk,
        'force_logout': True,
        'errors': [{
            'message': 'The email address is not verified.',
            'code': 'email_not_verified',
            'error_type': 'auth'
        }]
    }
    assert response.cookies['greenbudgetjwt'].value == ''


def test_validate_token_missing_token(api_client):
    response = api_client.post("/v1/jwt/validate/")
    assert response.status_code == 403
    assert response.json() == {
        'errors': [{
            'message': 'User is not authenticated.',
            'code': 'account_not_authenticated',
            'error_type': 'auth'
        }]
    }
    assert 'greenbudgetjwt' not in response.cookies


def test_validate_token_missing_token_logged_in(api_client, user):
    api_client.force_login(user)
    response = api_client.post("/v1/jwt/validate/")
    assert response.status_code == 403
    assert response.json() == {
        'force_logout': True,
        'user_id': user.id,
        'errors': [{
            'message': 'Token is invalid.',
            'code': 'token_not_valid',
            'error_type': 'auth'
        }]
    }
    assert response.cookies['greenbudgetjwt'].value == ''


def test_validate_token_invalid_token(api_client, settings):
    api_client.cookies = SimpleCookie({
        settings.JWT_TOKEN_COOKIE_NAME: "invalid-token"
    })
    response = api_client.post("/v1/jwt/validate/")
    assert response.status_code == 403
    assert response.json() == {
        'force_logout': True,
        'errors': [{
            'message': 'Token is invalid.',
            'code': 'token_not_valid',
            'error_type': 'auth'
        }]
    }
    assert response.cookies['greenbudgetjwt'].value == ''


def test_validate_token_invalid_token_logged_in(api_client, user, settings):
    api_client.force_login(user)
    api_client.cookies = SimpleCookie({
        settings.JWT_TOKEN_COOKIE_NAME: "invalid-token"
    })
    response = api_client.post("/v1/jwt/validate/")
    assert response.status_code == 403
    assert response.json() == {
        'force_logout': True,
        'user_id': 1,
        'errors': [{
            'message': 'Token is invalid.',
            'code': 'token_not_valid',
            'error_type': 'auth'
        }]
    }
    assert response.cookies['greenbudgetjwt'].value == ''
