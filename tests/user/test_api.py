import mock
from django.test import override_settings
import pytest

from greenbudget.app.authentication.tokens import AccessToken


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
@override_settings(
    EMAIL_ENABLED=True,
    FROM_EMAIL="noreply@greenbudget.io",
    FRONTEND_EMAIL_CONFIRM_URL="https://app.greenbudget.io/verify"
)
def test_registration(api_client, models, settings, user):
    # Use another user to generate the Access Token for mock purposes.
    token = AccessToken.for_user(user)

    def create_token(user):
        return token

    with mock.patch.object(AccessToken, 'for_user', create_token):
        with mock.patch('greenbudget.app.authentication.mail.send_mail') as m:
            response = api_client.post("/v1/users/registration/", data={
                "first_name": "Jack",
                "last_name": "Johnson",
                "password": "hoopla@H9_12",
                "email": "jjohnson@gmail.com",
            })
            assert response.status_code == 201
            assert response.json() == {
                "id": 2,
                "first_name": "Jack",
                "last_name": "Johnson",
                "email": "jjohnson@gmail.com",
                "is_active": True,
                "is_admin": False,
                "is_superuser": False,
                "is_staff": False,
                "company": None,
                "position": None,
                "address": None,
                "phone_number": None,
                "full_name": "Jack Johnson",
                "created_at": "2020-01-01 00:00:00",
                "updated_at": "2020-01-01 00:00:00",
                "last_login": None,
                "date_joined": "2020-01-01 00:00:00",
                "profile_image": None,
                "timezone": "America/New_York",
                "is_first_time": True,
            }

    assert m.called
    mail_obj = m.call_args[0][0]
    assert mail_obj.get() == {
        'from': {'email': "noreply@greenbudget.io"},
        'template_id': settings.EMAIL_VERIFICATION_TEMPLATE_ID,
        'personalizations': [
            {
                'to': [{'email': 'jjohnson@gmail.com'}],
                'dynamic_template_data': {
                    'redirect_url': (
                        'https://app.greenbudget.io/verify?token=%s'
                        % str(token)
                    )
                }
            }
        ]
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
        "company": user.company,
        "position": user.position,
        "address": user.address,
        "phone_number": user.phone_number,
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


@pytest.mark.freeze_time('2020-01-01')
def test_change_password(api_client, user, user_password):
    api_client.force_login(user)
    response = api_client.patch("/v1/users/change-password/", data={
        'password': user_password,
        "new_password": "hoopla@H9_124334",
    })
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "is_active": True,
        "is_admin": False,
        "is_superuser": False,
        "is_staff": False,
        "company": user.company,
        "position": user.position,
        "address": user.address,
        "phone_number": user.phone_number,
        "full_name": user.full_name,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "last_login": "2020-01-01 00:00:00",
        "date_joined": "2020-01-01 00:00:00",
        "profile_image": None,
        "timezone": str(user.timezone),
        "is_first_time": False,
    }

    user.refresh_from_db()
    assert user.check_password("hoopla@H9_124334")


@pytest.mark.freeze_time('2020-01-01')
def test_change_password_invalid_password(api_client, user):
    api_client.force_login(user)
    response = api_client.patch("/v1/users/change-password/", data={
        'password': 'hoopla',
        "new_password": "hoopla@H9_155",
    })
    assert response.status_code == 400
    assert response.json() == {
        'errors': [{
            'message': 'The provided password is invalid.',
            'code': 'invalid_credentials',
            'error_type': 'field',
            'field': 'password'
        }]
    }


@pytest.mark.parametrize("password", [
    'hoopla',  # Not 8 characters long
    'hoopla122412H',  # No special characters
    'hoopla@JJ',  # No numbers
    'hoopla123@',  # No capital letters
])
def test_change_password_invalid_new_password(api_client, password, user,
        user_password):
    api_client.force_login(user)
    response = api_client.patch("/v1/users/change-password/", data={
        "new_password": password,
        "password": user_password
    })
    assert response.status_code == 400
    assert response.json()['errors'][0]['field'] == 'new_password'
    assert response.json()['errors'][0]['code'] == 'invalid_password'
