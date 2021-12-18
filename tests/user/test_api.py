import mock
import pytest
import responses

from django.test import override_settings

from greenbudget.app.authentication.tokens import AccessToken
from greenbudget.app.user.mail import get_template


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
    FRONTEND_URL="https://app.greenbudget.io"
)
def test_registration(api_client, models, settings, user):
    # Use another user to generate the Access Token for mock purposes.
    token = AccessToken.for_user(user)

    def create_token(user):
        return token

    with mock.patch.object(AccessToken, 'for_user', create_token):
        with mock.patch('greenbudget.app.user.mail.send_mail') as m:
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
        'template_id': get_template("email_confirmation").id,
        'personalizations': [
            {
                'to': [{'email': 'jjohnson@gmail.com'}],
                'dynamic_template_data': {
                    'url': (
                        'https://app.greenbudget.io/verify?token=%s'
                        % str(token)
                    )
                }
            }
        ]
    }
    user = models.User.objects.get(pk=response.json()['id'])
    assert user.is_approved is True
    assert user.first_name == "Jack"
    assert user.last_name == "Johnson"
    assert user.email == "jjohnson@gmail.com"
    assert user.is_staff is False
    assert user.is_admin is False
    assert user.is_superuser is False
    assert user.is_active is True
    assert user.check_password("hoopla@H9_12") is True


@responses.activate
@override_settings(
    WAITLIST_ENABLED=True,
    SENDGRID_API_URL="https://api.fakesendgrid.com/v3/"
)
def test_registration_user_on_waitlist(api_client, models):
    responses.add(
        method=responses.POST,
        url="https://api.fakesendgrid.com/v3/marketing/contacts/search/emails",
        json={"result": {"jjohnson@gmail.com": {}}}
    )
    response = api_client.post("/v1/users/registration/", data={
        "first_name": "Jack",
        "last_name": "Johnson",
        "password": "hoopla@H9_12",
        "email": "jjohnson@gmail.com",
    })
    assert response.status_code == 201
    assert response.json()['email'] == 'jjohnson@gmail.com'
    user = models.User.objects.get(email="jjohnson@gmail.com")
    assert user.is_approved is False


@responses.activate
@override_settings(
    WAITLIST_ENABLED=True,
    SENDGRID_API_URL="https://api.fakesendgrid.com/v3/"
)
def test_registration_user_not_on_waitlist(api_client):
    responses.add(
        method=responses.POST,
        url="https://api.fakesendgrid.com/v3/marketing/contacts/search/emails",
        status=404
    )
    response = api_client.post("/v1/users/registration/", data={
        "first_name": "Jack",
        "last_name": "Johnson",
        "password": "hoopla@H9_12",
        "email": "jjohnson@gmail.com",
    })
    assert response.json() == {
        'errors': [{
            'message': 'The email address is not on the waitlist.',
            'code': 'account_not_on_waitlist',
            'error_type': 'auth'
        }]
    }


@responses.activate
@override_settings(
    WAITLIST_ENABLED=True,
    SENDGRID_API_URL="https://api.fakesendgrid.com/v3/"
)
def test_registration_waitlist_empty(api_client):
    responses.add(
        method=responses.POST,
        url="https://api.fakesendgrid.com/v3/marketing/contacts/search/emails",
        json={"result": {}}
    )
    response = api_client.post("/v1/users/registration/", data={
        "first_name": "Jack",
        "last_name": "Johnson",
        "password": "hoopla@H9_12",
        "email": "jjohnson@gmail.com",
    })
    assert response.json() == {
        'errors': [{
            'message': 'The email address is not on the waitlist.',
            'code': 'account_not_on_waitlist',
            'error_type': 'auth'
        }]
    }


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
