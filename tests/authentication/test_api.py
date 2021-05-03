from datetime import timedelta, datetime
import mock
import pytest
import responses

from django.test import override_settings

from greenbudget.lib.utils.dateutils import api_datetime_string
from greenbudget.app.authentication.models import ResetUID


def test_login(user, api_client):
    user.set_password("testpassword123")
    user.save()
    response = api_client.post("/v1/auth/login/", data={
        "email": user.email,
        "password": "testpassword123"
    })
    assert response.status_code == 201
    assert response.json() == {'detail': 'Successfully logged in.'}
    assert 'greenbudgetjwt' in response.cookies


def test_login_missing_password(user, api_client):
    response = api_client.post("/v1/auth/login/", data={
        "email": user.email,
    })
    assert response.status_code == 400
    assert 'greenbudgetjwt' not in response.cookies


def test_login_missing_email(user, api_client):
    response = api_client.post("/v1/auth/login/", data={
        "password": user.password,
    })
    assert response.status_code == 400
    assert 'greenbudgetjwt' not in response.cookies


def test_login_invalid_email(api_client, db):
    response = api_client.post("/v1/auth/login/", data={
        "email": "userdoesnotexist@gmail.com",
        "password": "fake-password",
    })
    assert response.status_code == 403
    assert 'greenbudgetjwt' not in response.cookies
    assert response.json() == {
        'errors': [{
            'message': 'The provided username does not exist in our system.',  # noqa
            'error_type': 'global',
            'code': 'email_does_not_exist'
        }]
    }


def test_login_invalid_password(user, api_client):
    response = api_client.post("/v1/auth/login/", data={
        "email": user.email,
        "password": "fake-password",
    })
    assert response.status_code == 403
    assert 'greenbudgetjwt' not in response.cookies
    assert response.json() == {
        'errors': [{
            'message': 'The provided password is invalid.',
            'error_type': 'global',
            'code': 'invalid_credentials'
        }]
    }


def test_logout(user, api_client):
    api_client.force_login(user)
    response = api_client.post("/v1/auth/logout/")
    assert response.status_code == 201
    assert response.cookies['greenbudgetjwt'].value == ""


@responses.activate
@override_settings(GOOGLE_OAUTH_API_URL="https://www.test-validate-user-token/")
def test_social_login_user_exists(api_client, create_user):
    create_user(email="jjohnson@gmail.com")
    responses.add(
        method=responses.GET,
        url="https://www.test-validate-user-token/?id_token=testtoken",
        json={
            "family_name": "Johnson",
            "given_name": "Jack",
            "email": "jjohnson@gmail.com"
        }
    )
    response = api_client.post("/v1/auth/social-login/", data={
        "token_id": "testtoken",
        'provider': 'google',
    })
    assert response.status_code == 201
    assert response.json() == {'detail': 'Successfully logged in.'}
    assert 'greenbudgetjwt' in response.cookies


@responses.activate
@override_settings(GOOGLE_OAUTH_API_URL="https://www.test-validate-user-token/")
def test_social_login_user_does_not_exist(api_client, models):
    responses.add(
        method=responses.GET,
        url="https://www.test-validate-user-token/?id_token=testtoken",
        json={
            "family_name": "Johnson",
            "given_name": "Jack",
            "email": "jjohnson@gmail.com"
        }
    )
    response = api_client.post("/v1/auth/social-login/", data={
        "token_id": "testtoken",
        'provider': 'google',
    })
    user = models.User.objects.filter(email="jjohnson@gmail.com").first()
    assert user is not None
    assert user.first_name == "Jack"
    assert user.last_name == "Johnson"

    assert response.status_code == 201
    assert response.json() == {'detail': 'Successfully logged in.'}
    assert 'greenbudgetjwt' in response.cookies


@responses.activate
@override_settings(GOOGLE_OAUTH_API_URL="https://www.test-validate-user-token/")
def test_social_login_invalid_token(api_client, create_user):
    create_user(email="jjohnson@gmail.com")
    responses.add(
        method=responses.GET,
        url="https://www.test-validate-user-token/?id_token=testtoken",
        json={
            "family_name": "Johnson",
            "given_name": "Jack",
            "email": "jjohnson@gmail.com"
        }
    )
    response = api_client.post("/v1/auth/social-login/", data={
        "token_id": "invalid",
        'provider': 'google',
    })
    assert response.status_code == 400
    assert 'greenbudgetjwt' not in response.cookies


@responses.activate
@override_settings(GOOGLE_OAUTH_API_URL="https://www.test-validate-user-token/")
def test_social_login_invalid_provider(api_client, create_user, db):
    create_user(email="jjohnson@gmail.com")
    responses.add(
        method=responses.GET,
        url="https://www.test-validate-user-token/?id_token=testtoken",
        json={
            "family_name": "Johnson",
            "given_name": "Jack",
            "email": "jjohnson@gmail.com"
        }
    )
    response = api_client.post("/v1/auth/social-login/", data={
        "token_id": "invalid",
        'provider': 'qanon',
    })
    assert response.status_code == 400
    assert 'greenbudgetjwt' not in response.cookies


def test_reset_password(user, api_client, db):
    reset_uid = ResetUID.objects.create(
        token="token1234567",
        used=False,
        user=user,
    )
    response = api_client.post("/v1/auth/reset-password/", data={
        "token": reset_uid.token,
        "password": "TestUserPassword4321$",
        "confirm": "TestUserPassword4321$",
    })
    user.refresh_from_db()
    assert response.status_code == 201
    assert response.json() == {
        'id': user.pk,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'full_name': user.full_name,
        'email': user.email,
        'username': user.username,
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
    }


def test_reset_password_invalid_token(api_client, db):
    response = api_client.post("/v1/auth/reset-password/", data={
        "token": "token1234567",
        "password": "TestUserPassword4321$",
        "confirm": "TestUserPassword4321$",
    })
    assert response.status_code == 403
    assert response.json() == {
        'errors': [{
            'error_type': 'global',
            'message': 'The provided token is invalid.',
            'code': 'invalid_reset_token'
        }]
    }


@override_settings(PWD_RESET_LINK_EXPIRY_TIME_IN_HRS=48)
@pytest.mark.freeze_time('2020-01-01')
def test_reset_password_token_expired(user, api_client, freezer):
    reset_uid = ResetUID.objects.create(
        token="token1234567",
        used=False,
        user=user,
    )
    # Move Forward in Time 5 Hours + 5 Minutes, Just After Expiry
    future_date = datetime(2020, 1, 1) + timedelta(minutes=60 * 48 + 5)
    freezer.move_to(future_date)

    response = api_client.post("/v1/auth/reset-password/", data={
        "token": reset_uid.token,
        "password": "TestUserPassword4321$",
        "confirm": "TestUserPassword4321$",
    })

    assert response.status_code == 403
    assert response.json() == {
        'errors': [{
            'error_type': 'global',
            'message': 'The password reset link has expired.',
            'code': 'password_reset_link_expired',
        }]
    }


@override_settings(
    RESET_PWD_UI_LINK="https://greenbudget.io/changepassword",
    FROM_EMAIL="greenbudget@gmail.com"
)
@pytest.mark.freeze_time('2020-01-01')
def test_forgot_password(user, api_client):
    # Mock the Email Generation
    # Note that we cannot mock the email sending to test the contents of the
    # email because the email contents are supplied as arguments in the
    # EmailMultiAlternatives __init__ method, not the send() method.  Mocking an
    # __init__ method properly is extremely difficult - so the best we can do
    # is mock the render_to_string method an d make sure the supplied arguments
    # are valid for the generated email.
    with mock.patch('greenbudget.app.user.utils.render_to_string') as mocked:  # noqa
        response = api_client.post("/v1/auth/forgot-password/", data={
            "email": user.email
        })

    assert response.status_code == 201

    assert ResetUID.objects.count() == 1
    reset_uid = ResetUID.objects.first()
    assert reset_uid.user == user

    # Test Email Was Sent
    assert mocked.called
    assert mocked.call_args[0][0] == 'email/forgot_password.html'
    assert mocked.call_args[0][1] == {
        'PWD_RESET_LINK': (
            'https://greenbudget.io/changepassword?token=%s'
            % reset_uid.token
        ),
        'from_email': "greenbudget@gmail.com",
        'EMAIL': user.email,
        'year': 2020,
        'NAME': "%s %s" % (user.first_name, user.last_name)
    }
