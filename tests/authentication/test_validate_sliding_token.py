from http.cookies import SimpleCookie
import pytest

from greenbudget.lib.utils.dateutils import api_datetime_string


@pytest.fixture
def validate_sliding_token(jwt_authenticated_client):
    def inner():
        return jwt_authenticated_client.post("/v1/auth/validate/")
    return inner


@pytest.mark.freeze_time('2020-01-01')
def test_validate_sliding_token(jwt_authenticated_client, validate_sliding_token,
        user, settings):
    jwt_authenticated_client.force_login(user)
    response = validate_sliding_token()
    assert response.status_code == 201
    assert settings.JWT_TOKEN_COOKIE_NAME in response.cookies

    assert response.json() == {
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


@pytest.mark.freeze_time('2020-01-01')
def test_force_logout_on_sliding_token_removal(jwt_authenticated_client, user,
        validate_sliding_token, settings):
    jwt_authenticated_client.force_login(user)
    response = validate_sliding_token()
    assert response.status_code == 201
    assert settings.JWT_TOKEN_COOKIE_NAME in response.cookies

    jwt_authenticated_client.logout()
    response = jwt_authenticated_client.get("/v1/budgets/")
    assert response.status_code == 403


def test_validate_sliding_token_inactive_user(inactive_user, settings,
        validate_sliding_token, jwt_authenticated_client):
    jwt_authenticated_client.force_login(inactive_user)
    response = validate_sliding_token()
    assert response.status_code == 403
    assert response.json() == {
        'user_id': inactive_user.pk,
        'force_logout': True,
        'errors': [{
            'message': 'Your account is not active, please contact customer care.',  # noqa
            'code': 'account_disabled',
            'error_type': 'auth'
        }]
    }
    assert response.cookies[settings.JWT_TOKEN_COOKIE_NAME].value == ''


def test_validate_sliding_token_unverified_user(validate_sliding_token,
        unverified_user, jwt_authenticated_client, settings):
    jwt_authenticated_client.force_login(unverified_user)
    response = validate_sliding_token()
    assert response.status_code == 403
    assert response.json() == {
        'user_id': unverified_user.pk,
        'force_logout': True,
        'errors': [{
            'message': 'The email address is not verified.',
            'code': 'email_not_verified',
            'error_type': 'auth'
        }]
    }
    assert response.cookies[settings.JWT_TOKEN_COOKIE_NAME].value == ''


def test_validate_sliding_token_missing_token(api_client, user, settings):
    api_client.force_login(user)
    response = api_client.post("/v1/auth/validate/")
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
    assert response.cookies[settings.JWT_TOKEN_COOKIE_NAME].value == ''


def test_validate_sliding_token_invalid_token(api_client, user, settings):
    api_client.force_login(user)
    api_client.cookies = SimpleCookie({
        settings.JWT_TOKEN_COOKIE_NAME: "invalid-token"
    })
    response = api_client.post("/v1/auth/validate/")
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
    assert response.cookies[settings.JWT_TOKEN_COOKIE_NAME].value == ''
