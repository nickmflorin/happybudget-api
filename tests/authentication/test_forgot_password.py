from datetime import timedelta, datetime

import pytest
from django.test import override_settings

from greenbudget.lib.utils.dateutils import api_datetime_string
from greenbudget.app.authentication.tokens import AccessToken


@pytest.fixture
def validate_password_token(api_client, user):
    def inner():
        token = AccessToken.for_user(user)
        return api_client.post(
            "/v1/auth/validate-forgot-password-token/",
            data={"token": str(token)}
        )
    return inner


@pytest.mark.freeze_time('2020-01-01')
def test_validate_password_token(validate_password_token, user):
    response = validate_password_token()
    assert response.status_code == 201
    user.refresh_from_db()
    assert user.is_verified
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
            'last_login': None,
            'timezone': str(user.timezone),
            "profile_image": None,
            "is_first_time": False
        }
    }


@pytest.mark.freeze_time('2021-01-03')
@override_settings(ACCESS_TOKEN_LIFETIME=timedelta(hours=24))
def test_verify_email_expired_token(api_client, unverified_user):
    token = AccessToken.for_user(unverified_user)
    token.set_exp(claim='exp', from_time=datetime(2021, 1, 1))
    response = api_client.post(
        "/v1/auth/validate-forgot-password-token/",
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


def test_validate_password_token_inactive_user(inactive_user,
        validate_password_token):
    response = validate_password_token()
    assert response.status_code == 403
    assert response.json() == {
        'user_id': inactive_user.pk,
        'errors': [{
            'message': 'Your account is not active, please contact customer care.',  # noqa
            'code': 'account_disabled',
            'error_type': 'auth'
        }]
    }


def test_validate_password_token_unverified_user(unverified_user,
        validate_password_token):
    response = validate_password_token()
    assert response.status_code == 403
    assert response.json() == {
        'user_id': unverified_user.pk,
        'errors': [{
            'message': 'The email address is not verified.',
            'code': 'email_not_verified',
            'error_type': 'auth'
        }]
    }


def test_validate_password_token_user_logged_in(validate_password_token,
        api_client, inactive_user):
    api_client.force_login(inactive_user)
    response = validate_password_token()
    assert response.status_code == 403
    assert response.json() == {
        'errors': [{
            'message': 'User already has an active session.',
            'code': 'permission_denied',
            'error_type': 'auth'
        }]
    }


def test_validate_password_token_missing_token(api_client):
    response = api_client.post("/v1/auth/validate-forgot-password-token/")
    assert response.status_code == 403
    assert response.json() == {
        'errors': [{
            'message': 'Token is invalid.',
            'code': 'token_not_valid',
            'error_type': 'auth'
        }]
    }


def test_validate_password_token_invalid_token(api_client):
    response = api_client.post(
        "/v1/auth/validate-forgot-password-token/",
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


@pytest.mark.freeze_time('2020-01-01')
def test_forgot_password(user, api_client):
    response = api_client.post("/v1/auth/forgot-password/", data={
        "email": user.email
    })
    assert response.status_code == 201

# def test_reset_password(user_with_password, api_client):
#     reset_uid = ResetUID.objects.create(
#         token="token1234567",
#         used=False,
#         user=user_with_password,
#     )
#     response = api_client.post("/v1/auth/reset-password/", data={
#         "token": reset_uid.token,
#         "password": "TestUserPassword4321$",
#         "confirm": "TestUserPassword4321$",
#     })
#     user_with_password.refresh_from_db()
#     assert response.status_code == 201
#     assert response.json() == {
#         'id': user_with_password.pk,
#         'first_name': user_with_password.first_name,
#         'last_name': user_with_password.last_name,
#         'full_name': user_with_password.full_name,
#         'email': user_with_password.email,
#         'is_active': user_with_password.is_active,
#         'is_admin': user_with_password.is_admin,
#         'is_superuser': user_with_password.is_superuser,
#         'is_staff': user_with_password.is_staff,
#         'date_joined': api_datetime_string(user_with_password.date_joined),
#         'updated_at': api_datetime_string(user_with_password.updated_at),
#         'created_at': api_datetime_string(user_with_password.created_at),
#         'last_login': None,
#         'timezone': str(user_with_password.timezone),
#         "profile_image": None,
#         "is_first_time": False,
#     }


# @pytest.mark.parametrize("password", [
#     'hoopla',  # Not 8 characters long
#     'hoopla122412H',  # No special characters
#     'hoopla@JJ',  # No numbers
#     'hoopla123@',  # No capital letters
# ])
# def test_reset_password_invalid_password(api_client, user, password):
#     reset_uid = ResetUID.objects.create(
#         token="token1234567",
#         used=False,
#         user=user,
#     )
#     response = api_client.post("/v1/auth/reset-password/", data={
#         "token": reset_uid.token,
#         "password": password,
#         "confirm": password,
#     })
#     assert response.status_code == 400
#     assert response.json()['errors'][0]['field'] == 'password'
#     assert response.json()['errors'][0]['code'] == 'invalid_password'


# def test_reset_password_invalid_token(api_client):
#     response = api_client.post("/v1/auth/reset-password/", data={
#         "token": "token1234567",
#         "password": "hoopla@H9_12$",
#         "confirm": "hoopla@H9_12$",
#     })
#     assert response.status_code == 400
#     assert response.json()['errors'][0]['code'] == 'does_not_exist'


# @override_settings(PWD_RESET_LINK_EXPIRY_TIME_IN_HRS=48)
# @pytest.mark.freeze_time('2020-01-01')
# def test_reset_password_token_expired(user, api_client, freezer):
#     reset_uid = ResetUID.objects.create(
#         token="token1234567",
#         used=False,
#         user=user,
#     )
#     # Move Forward in Time 5 Hours + 5 Minutes, Just After Expiry
#     future_date = datetime(2020, 1, 1) + timedelta(minutes=60 * 48 + 5)
#     freezer.move_to(future_date)

#     response = api_client.post("/v1/auth/reset-password/", data={
#         "token": reset_uid.token,
#         "password": "hoopla@H9_12$",
#         "confirm": "hoopla@H9_12$",
#     })
#     assert response.status_code == 400
#     assert response.json() == {
#         'errors': [{
#             'message': 'Token has expired.',
#             'code': 'invalid',
#             'error_type': 'field',
#             'field': 'token'
#         }]
#     }
