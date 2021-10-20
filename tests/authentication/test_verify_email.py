from datetime import timedelta, datetime

import pytest
from django.test import override_settings

from greenbudget.lib.utils.dateutils import api_datetime_string
from greenbudget.app.authentication.tokens import AccessToken


@pytest.fixture
def validate_email_token(api_client, user):
    def inner():
        token = AccessToken.for_user(user)
        return api_client.post(
            "/v1/auth/validate-email-verification-token/",
            data={"token": str(token)}
        )
    return inner


@pytest.mark.freeze_time('2020-01-01')
def test_validate_email_token(validate_email_token, unverified_user):
    response = validate_email_token()
    assert response.status_code == 201
    unverified_user.refresh_from_db()
    assert unverified_user.is_verified
    assert response.json() == {
        'id': unverified_user.pk,
        'first_name': unverified_user.first_name,
        'last_name': unverified_user.last_name,
        'full_name': unverified_user.full_name,
        'email': unverified_user.email,
        'is_active': unverified_user.is_active,
        'is_admin': unverified_user.is_admin,
        'is_superuser': unverified_user.is_superuser,
        'is_staff': unverified_user.is_staff,
        'date_joined': api_datetime_string(unverified_user.date_joined),
        'updated_at': api_datetime_string(unverified_user.updated_at),
        'created_at': api_datetime_string(unverified_user.created_at),
        'last_login': None,
        'timezone': str(unverified_user.timezone),
        "profile_image": None,
        "is_first_time": False
    }


@pytest.mark.freeze_time('2021-01-03')
@override_settings(ACCESS_TOKEN_LIFETIME=timedelta(hours=24))
def test_verify_email_expired_token(api_client, unverified_user):
    token = AccessToken.for_user(unverified_user)
    token.set_exp(claim='exp', from_time=datetime(2021, 1, 1))
    response = api_client.post(
        "/v1/auth/validate-email-verification-token/",
        data={"token": str(token)}
    )
    assert response.json() == {
        'user_id': unverified_user.id,
        'errors': [{
            'message': 'The provided token is expired.',
            'code': 'token_expired',
            'error_type': 'auth'
        }]
    }


def test_validate_email_token_inactive_user(inactive_user, validate_email_token):
    inactive_user.is_verified = False
    inactive_user.save()
    response = validate_email_token()
    assert response.status_code == 403
    assert response.json() == {
        'user_id': inactive_user.pk,
        'errors': [{
            'message': 'Your account is not active, please contact customer care.',  # noqa
            'code': 'account_disabled',
            'error_type': 'auth'
        }]
    }


def test_validate_email_token_user_logged_in(validate_email_token,
        api_client, inactive_user):
    api_client.force_login(inactive_user)
    response = validate_email_token()
    assert response.status_code == 403
    assert response.json() == {
        'user_id': inactive_user.pk,
        'errors': [{
            'message': 'User already has an active session.',
            'code': 'permission_denied',
            'error_type': 'auth'
        }]
    }


def test_validate_email_token_missing_token(api_client):
    response = api_client.post("/v1/auth/validate-email-verification-token/")
    assert response.status_code == 403
    assert response.json() == {
        'errors': [{
            'message': 'Token is invalid.',
            'code': 'token_not_valid',
            'error_type': 'auth'
        }]
    }


def test_validate_email_token_invalid_token(api_client):
    response = api_client.post(
        "/v1/auth/validate-email-verification-token/",
        data={"token": "hoopla"}
    )
    assert response.status_code == 403
    assert response.json() == {
        'errors': [{
            'message': 'Token is invalid.',
            'code': 'token_not_valid',
            'error_type': 'auth'
        }]
    }


def test_send_verification_email(api_client, user):
    user.is_verified = False
    user.save()
    response = api_client.post("/v1/auth/verify-email/", data={
        "user": user.pk
    })
    assert response.status_code == 201


def test_send_verification_email_verified_user(api_client, user):
    response = api_client.post("/v1/auth/verify-email/", data={
        "user": user.pk
    })
    assert response.status_code == 400


def test_send_verification_email_inactive_user(api_client, user):
    user.is_active = False
    user.save()
    response = api_client.post("/v1/auth/verify-email/", data={
        "user": user.pk
    })
    assert response.status_code == 400
