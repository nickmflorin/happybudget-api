from http.cookies import SimpleCookie

from django.test import override_settings
import pytest

from happybudget.lib.utils.dateutils import api_datetime_string
from happybudget.app.authentication.tokens import AuthToken


@pytest.mark.freeze_time('2020-01-01')
@override_settings(BILLING_ENABLED=True)
def test_validate_auth_token(api_client, settings, standard_product_user):
    token = AuthToken.for_user(standard_product_user)
    api_client.cookies = SimpleCookie({
        settings.JWT_TOKEN_COOKIE_NAME: str(token),
    })
    api_client.force_login(standard_product_user)
    response = api_client.post("/v1/auth/validate/")
    assert response.status_code == 201
    assert settings.JWT_TOKEN_COOKIE_NAME in response.cookies

    assert response.json() == {
        'id': standard_product_user.pk,
        'first_name': standard_product_user.first_name,
        'last_name': standard_product_user.last_name,
        'full_name': standard_product_user.full_name,
        'email': standard_product_user.email,
        'is_active': standard_product_user.is_active,
        'is_superuser': standard_product_user.is_superuser,
        'is_staff': standard_product_user.is_staff,
        "company": standard_product_user.company,
        "position": standard_product_user.position,
        "address": standard_product_user.address,
        "phone_number": standard_product_user.phone_number,
        'date_joined': api_datetime_string(standard_product_user.date_joined),
        'last_login': '2020-01-01 00:00:00',
        'timezone': str(standard_product_user.timezone),
        "profile_image": None,
        "is_first_time": False,
        "product_id": "happybudget_standard",
        "billing_status": "active",
        "metrics": {
            "num_budgets": 0,
            "num_templates": 0,
            "num_collaborating_budgets": 0,
            "num_archived_budgets": 0
        }
    }


@override_settings(BILLING_ENABLED=True)
def test_validate_auth_token_twice_fetches_from_stripe_once(settings,
        api_client, mock_stripe, standard_product_user):
    token = AuthToken.for_user(standard_product_user)
    api_client.cookies = SimpleCookie({
        settings.JWT_TOKEN_COOKIE_NAME: str(token),
    })
    api_client.force_login(standard_product_user)

    response = api_client.post("/v1/auth/validate/")
    assert response.status_code == 201
    assert settings.JWT_TOKEN_COOKIE_NAME in response.cookies
    assert response.json()['product_id'] == 'happybudget_standard'
    assert response.json()['billing_status'] == 'active'

    response = api_client.post("/v1/auth/validate/")
    assert response.status_code == 201
    assert settings.JWT_TOKEN_COOKIE_NAME in response.cookies
    assert response.json()['product_id'] == 'happybudget_standard'
    assert response.json()['billing_status'] == 'active'

    assert mock_stripe.Customer.retrieve.call_count == 1


def test_force_logout_on_auth_token_removal(jwt_authenticated_client, user,
        settings):
    jwt_authenticated_client.force_login(user)
    response = jwt_authenticated_client.post("/v1/auth/validate/")
    assert response.status_code == 201
    assert settings.JWT_TOKEN_COOKIE_NAME in response.cookies

    jwt_authenticated_client.logout()
    response = jwt_authenticated_client.get("/v1/budgets/")
    assert response.status_code == 401


def test_validate_auth_token_not_logged_in(settings, jwt_authenticated_client):
    response = jwt_authenticated_client.post("/v1/auth/validate/")
    assert response.status_code == 401
    assert response.json() == {'errors': [{
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }]}
    assert settings.JWT_TOKEN_COOKIE_NAME not in response.cookies


def test_validate_auth_token_inactive_user(inactive_user, settings,
        jwt_authenticated_client):
    jwt_authenticated_client.force_login(inactive_user)
    response = jwt_authenticated_client.post("/v1/auth/validate/")
    assert response.status_code == 401
    assert response.json() == {
        'errors': [{
            'message': 'The account is not active.',
            'code': 'account_disabled',
            'error_type': 'auth',
            'user_id': inactive_user.pk
        }]
    }
    assert settings.JWT_TOKEN_COOKIE_NAME not in response.cookies


@override_settings(EMAIL_VERIFICATION_ENABLED=True)
def test_validate_auth_token_unverified_user(unverified_user, settings,
        jwt_authenticated_client):
    jwt_authenticated_client.force_login(unverified_user)
    response = jwt_authenticated_client.post("/v1/auth/validate/")
    assert response.status_code == 401
    assert response.json() == {
        'errors': [{
            'message': 'The email address is not verified.',
            'code': 'account_not_verified',
            'error_type': 'auth',
            'user_id': unverified_user.pk,
        }]
    }
    assert settings.JWT_TOKEN_COOKIE_NAME not in response.cookies


def test_validate_auth_token_missing_token(api_client, user, settings):
    api_client.force_login(user)
    response = api_client.post("/v1/auth/validate/")
    assert response.status_code == 401
    assert settings.JWT_TOKEN_COOKIE_NAME not in response.cookies


def test_validate_auth_token_invalid_token(api_client, user, settings):
    api_client.cookies = SimpleCookie({
        settings.JWT_TOKEN_COOKIE_NAME: "invalid-token"
    })
    api_client.force_login(user)
    response = api_client.post("/v1/auth/validate/")
    assert response.status_code == 401
    assert response.json() == {
        'errors': [{
            'message': 'Token is invalid.',
            'code': 'token_not_valid',
            'error_type': 'auth',
            'user_id': 1
        }]
    }
    assert settings.JWT_TOKEN_COOKIE_NAME not in response.cookies
