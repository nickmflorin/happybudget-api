import datetime
from django.test import override_settings
import pytest

from greenbudget.app.jwt.tokens import GreenbudgetEmailVerificationSlidingToken


@pytest.mark.parametrize("password", [
    'hoopla',  # Not 8 characters long
    'hoopla122412H',  # No special characters
    'hoopla@JJ',  # No numbers
    'hoopla123@',  # No capital letters
])
def test_registration_invalid_password(api_client, password):
    response = api_client.post("/v1/users/registration/", data={
        "first_name": "Jack",
        "last_name": "Johnson",
        "password": password,
        "email": "jjohnson@gmail.com",
    })
    assert response.status_code == 400
    assert response.json()['errors'][0]['field'] == 'password'
    assert response.json()['errors'][0]['code'] == 'invalid_password'


@pytest.mark.freeze_time('2020-01-01')
def test_registration(api_client, models):
    response = api_client.post("/v1/users/registration/", data={
        "first_name": "Jack",
        "last_name": "Johnson",
        "password": "hoopla@H9_12",
        "email": "jjohnson@gmail.com",
    })
    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "first_name": "Jack",
        "last_name": "Johnson",
        "email": "jjohnson@gmail.com",
        "is_active": True,
        "is_admin": False,
        "is_superuser": False,
        "is_staff": False,
        "full_name": "Jack Johnson",
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "last_login": "2020-01-01 00:00:00",
        "date_joined": "2020-01-01 00:00:00",
        "profile_image": None,
        "timezone": "America/New_York",
        "is_first_time": True,
    }
    user = models.User.objects.get(pk=response.json()['id'])
    assert user.first_name == "Jack"
    assert user.last_name == "Johnson"
    assert user.email == "jjohnson@gmail.com"
    assert user.is_staff is False
    assert user.is_admin is False
    assert user.is_superuser is False
    assert user.is_active is True
    assert user.check_password("hoopla@H9_12") is True

    # The user should be saved as not being first time anymore, but the response
    # should indicate that it was their first time logging in.
    assert user.is_first_time is False


@pytest.mark.freeze_time('2020-01-01')
def test_update_logged_in_user(api_client, user):
    api_client.force_login(user)
    response = api_client.patch("/v1/users/user/", data={
        'first_name': 'New First Name',
        'last_name': 'New Last Name'
    })
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "first_name": "New First Name",
        "last_name": "New Last Name",
        "email": user.email,
        "is_active": True,
        "is_admin": False,
        "is_superuser": False,
        "is_staff": False,
        "full_name": "New First Name New Last Name",
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "last_login": "2020-01-01 00:00:00",
        "date_joined": "2020-01-01 00:00:00",
        "profile_image": None,
        "timezone": str(user.timezone),
        "is_first_time": False,
    }

    user.refresh_from_db()
    assert user.first_name == "New First Name"
    assert user.last_name == "New Last Name"


def test_verify_email(api_client, user):
    user.is_verified = False
    user.save()
    token = GreenbudgetEmailVerificationSlidingToken.for_user(user)
    response = api_client.post("/v1/users/verify-email/", data={
        "token": str(token)
    })
    assert response.status_code == 201
    user.refresh_from_db()
    assert user.is_verified


@pytest.mark.freeze_time('2021-01-03')
@override_settings(EMAIL_VERIFICATION_JWT_EXPIRY=datetime.timedelta(hours=24))
def test_verify_email_expired_token(api_client, user):
    token = GreenbudgetEmailVerificationSlidingToken.for_user(user)
    token.set_exp(claim='refresh_exp', from_time=datetime.datetime(2021, 1, 1))
    response = api_client.post("/v1/users/verify-email/", data={
        "token": str(token)
    })
    assert response.json() == {
        'user_id': user.id,
        'errors': [{
            'message': 'The provided token is expired.',
            'code': 'token_expired',
            'error_type': 'auth'
        }]
    }


def test_verify_email_user_does_not_exist(api_client, user):
    token = GreenbudgetEmailVerificationSlidingToken.for_user(user)
    user.delete()
    response = api_client.post("/v1/users/verify-email/", data={
        "token": str(token)
    })
    assert response.status_code == 403
    assert response.json() == {
        'errors': [{
            'message': 'Token is invalid.',
            'code': 'token_not_valid',
            'error_type': 'auth'
        }]
    }


def test_verify_email_invalid_token(api_client):
    response = api_client.post("/v1/users/verify-email/", data={
        "token": "hoopla",
    })
    assert response.status_code == 403
    assert response.json() == {
        'errors': [{
            'message': 'Token is invalid.',
            'code': 'token_not_valid',
            'error_type': 'auth'
        }]
    }
