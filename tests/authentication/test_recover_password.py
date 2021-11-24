from datetime import timedelta, datetime
import mock

import pytest
from django.test import override_settings

from greenbudget.lib.utils.dateutils import api_datetime_string
from greenbudget.app.authentication.tokens import AccessToken


VALID_PASSWORD = "hoopla@H9_12$"


@pytest.mark.freeze_time('2020-01-01')
def test_validate_password_token(api_client, user):
    token = AccessToken.for_user(user)
    response = api_client.post(
        "/v1/auth/validate-password-recovery-token/",
        data={"token": str(token)}
    )
    assert response.status_code == 201
    user.refresh_from_db()
    assert user.is_verified
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
        "company": user.company,
        "position": user.position,
        "address": user.address,
        "phone_number": user.phone_number,
        'date_joined': api_datetime_string(user.date_joined),
        'last_login': None,
        'timezone': str(user.timezone),
        "profile_image": None,
        "is_first_time": False
    }


@pytest.mark.freeze_time('2021-01-03')
@override_settings(ACCESS_TOKEN_LIFETIME=timedelta(hours=24))
@pytest.mark.parametrize("path,extra_data", [
    ("validate-password-recovery-token", {}),
    ("reset-password", {"password": VALID_PASSWORD})
])
def test_password_recovery_expired_token(api_client, user, path, extra_data):
    token = AccessToken.for_user(user)
    token.set_exp(claim='exp', from_time=datetime(2021, 1, 1))
    response = api_client.post("/v1/auth/%s/" % path, data={**extra_data, **{
        "token": str(token)
    }})
    assert response.json() == {
        'user_id': user.id,
        'errors': [{
            'message': 'The provided token is expired.',
            'code': 'token_expired',
            'error_type': 'auth'
        }]
    }


@pytest.mark.parametrize("path,extra_data", [
    ("validate-password-recovery-token", {}),
    ("reset-password", {"password": VALID_PASSWORD})
])
def test_password_recovery_inactive_user(inactive_user, api_client, path,
        extra_data):
    token = AccessToken.for_user(inactive_user)
    response = api_client.post("/v1/auth/%s/" % path, data={**extra_data, **{
        "token": str(token)
    }})
    assert response.status_code == 403
    assert response.json() == {
        'user_id': inactive_user.pk,
        'errors': [{
            'message': 'Your account is not active, please contact customer care.',  # noqa
            'code': 'account_disabled',
            'error_type': 'auth'
        }]
    }


@pytest.mark.parametrize("path,extra_data", [
    ("validate-password-recovery-token", {}),
    ("reset-password", {"password": VALID_PASSWORD})
])
def test_password_recovery_unverified_user(unverified_user, api_client, path,
        extra_data):
    token = AccessToken.for_user(unverified_user)
    response = api_client.post("/v1/auth/%s/" % path, data={**extra_data, **{
        "token": str(token)
    }})
    assert response.json() == {
        'user_id': unverified_user.pk,
        'errors': [{
            'message': 'The email address is not verified.',
            'code': 'email_not_verified',
            'error_type': 'auth'
        }]
    }


@pytest.mark.parametrize("path,extra_data", [
    ("validate-password-recovery-token", {}),
    ("reset-password", {"password": VALID_PASSWORD})
])
def test_password_recovery_user_logged_in(api_client, user, path, extra_data):
    api_client.force_login(user)
    token = AccessToken.for_user(user)
    response = api_client.post("/v1/auth/%s/" % path, data={**extra_data, **{
        "token": str(token)
    }})
    assert response.status_code == 403
    assert response.json() == {
        'user_id': user.pk,
        'errors': [{
            'message': 'User already has an active session.',
            'code': 'permission_denied',
            'error_type': 'auth'
        }]
    }


@pytest.mark.parametrize("path,extra_data", [
    ("validate-password-recovery-token", {}),
    ("reset-password", {"password": VALID_PASSWORD})
])
def test_password_recovery_missing_token(api_client, path, extra_data):
    response = api_client.post("/v1/auth/%s/" % path, data=extra_data)
    assert response.status_code == 403
    assert response.json() == {
        'errors': [{
            'message': 'Token is invalid.',
            'code': 'token_not_valid',
            'error_type': 'auth'
        }]
    }


@pytest.mark.parametrize("path,extra_data", [
    ("validate-password-recovery-token", {}),
    ("reset-password", {"password": VALID_PASSWORD})
])
def test_password_recovery_invalid_token(api_client, path, extra_data):
    response = api_client.post("/v1/auth/%s/" % path, data={**extra_data, **{
        "token": 'hoopla'
    }})
    assert response.status_code == 403
    assert response.json() == {
        'errors': [{
            'message': 'Token is invalid.',
            'code': 'token_not_valid',
            'error_type': 'auth'
        }]
    }


@override_settings(
    EMAIL_ENABLED=True,
    FROM_EMAIL="noreply@greenbudget.io",
    FRONTEND_PASSWORD_RECOVERY_URL="https://app.greenbudget.io/recovery"
)
def test_recover_password(user, api_client, settings):
    # Use another user to generate the Access Token for mock purposes.
    token = AccessToken.for_user(user)

    def create_token(user):
        return token

    with mock.patch.object(AccessToken, 'for_user', create_token):
        with mock.patch('greenbudget.app.authentication.mail.send_mail') as m:
            response = api_client.post("/v1/auth/recover-password/", data={
                "email": user.email
            })
    assert response.status_code == 201
    assert m.called
    mail_obj = m.call_args[0][0]
    assert mail_obj.get() == {
        'from': {'email': "noreply@greenbudget.io"},
        'template_id': settings.PASSWORD_RECOVERY_TEMPLATE_ID,
        'personalizations': [
            {
                'to': [{'email': user.email}],
                'dynamic_template_data': {
                    'redirect_url': (
                        'https://app.greenbudget.io/recovery?token=%s'
                        % str(token)
                    )
                }
            }
        ]
    }


def test_reset_password(user, api_client):
    token = AccessToken.for_user(user)
    response = api_client.post("/v1/auth/reset-password/", data={
        "token": str(token),
        "password": "TestUserPassword4321$",
    })
    user.refresh_from_db()
    assert response.status_code == 201
    assert user.check_password("TestUserPassword4321$")
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
        "company": user.company,
        "position": user.position,
        "address": user.address,
        "phone_number": user.phone_number,
        'date_joined': api_datetime_string(user.date_joined),
        'last_login': None,
        'timezone': str(user.timezone),
        "profile_image": None,
        "is_first_time": False,
    }


@pytest.mark.parametrize("password", [
    'hoopla',  # Not 8 characters long
    'hoopla122412H',  # No special characters
    'hoopla@JJ',  # No numbers
    'hoopla123@',  # No capital letters
])
def test_reset_password_invalid_password(api_client, user, password):
    token = AccessToken.for_user(user)
    response = api_client.post("/v1/auth/reset-password/", data={
        "token": str(token),
        "password": password
    })
    assert response.status_code == 400
    assert response.json()['errors'][0]['field'] == 'password'
    assert response.json()['errors'][0]['code'] == 'invalid_password'
