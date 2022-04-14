# pylint: disable=redefined-outer-name
import datetime
import mock
import pytest

from django.test import override_settings

from greenbudget.lib.utils.urls import add_query_params_to_url

from greenbudget.app.authentication.tokens import AccessToken
from greenbudget.app.user.mail import get_template


@pytest.fixture
def searchable_users(create_user):
    return [
        create_user(
            email="bcosby@gmail.com",
            first_name="Bill",
            last_name="Cosby",
            last_login=datetime.datetime(2020, 4, 1)
        ),
        create_user(
            email="slapattheoscars@gmail.com",
            first_name="Will",
            last_name="Smith",
            last_login=datetime.datetime(2020, 3, 1)
        ),
        create_user(
            email="wsmith@gmail.com",
            first_name="Will",
            last_name="Smith",
            last_login=datetime.datetime(2020, 2, 1)
        ),
        create_user(
            email="bjohnson@gmail.com",
            first_name="Will",
            last_name='Jackson',
            last_login=datetime.datetime(2020, 1, 1)
        ),
    ]


def test_search_users_no_search_term(api_client, user):
    api_client.force_login(user)

    # Not providing the search term should be prohibited, as we do not want to
    # allow a blanket search of all the users in the application.
    response = api_client.get("/v1/users/")
    assert response.status_code == 400
    assert response.json() == {'errors': [{
        'message': 'The search parameter is required.',
        'code': 'bad_request',
        'error_type': 'bad_request'
    }]}


@pytest.mark.parametrize('search,expected,exclude', [
    ('bcosby@gmail.com', [0], None),
    ('bill', [], None),
    ('bill cosby', [0], None),
    ('bjohnson', [], None),
    ('smith', [], None),
    ('Will', [], None),
    ('Will Smith', [1, 2], None),
    ('Jackson', [], None),
    ('Will Smith', [1], [4]),
])
def test_search_users(api_client, user, search, expected, searchable_users,
        exclude):
    api_client.force_login(user)
    url = add_query_params_to_url(
        url="/v1/users/", search=search, exclude=exclude)
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json()['count'] == len(expected)
    assert response.json()['data'] == [{
        'id': searchable_users[i].pk,
        'first_name': searchable_users[i].first_name,
        'last_name': searchable_users[i].last_name,
        'full_name': searchable_users[i].full_name,
        'email': searchable_users[i].email,
        'profile_image': None
    } for i in expected]


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
                "billing_status": None,
                "product_id": None,
                "metrics": {
                    "num_budgets": 0,
                    "num_templates": 0,
                    "num_collaborating_budgets": 0,
                    "num_archived_budgets": 0
                }
            }

    assert m.called
    mail_obj = m.call_args[0][0]
    assert mail_obj.to == [{'email': "jjohnson@gmail.com"}]
    assert mail_obj.template_id == get_template("email_verification").id
    assert mail_obj.params == {
        'redirect_url': (
            'https://app.greenbudget.io/verify?token=%s' % str(token)
        )
    }
    user = models.User.objects.get(pk=response.json()['id'])
    assert user.first_name == "Jack"
    assert user.last_name == "Johnson"
    assert user.email == "jjohnson@gmail.com"
    assert user.is_staff is False
    assert user.is_superuser is False
    assert user.is_active is True
    assert user.check_password("hoopla@H9_12") is True


@override_settings(WAITLIST_ENABLED=True)
def test_registration_user_on_waitlist(api_client):
    mock_response = mock.MagicMock()
    mock_response.contacts = [{
        "email": "jjohnson@gmail.com",
        "emailBlacklisted": False
    }]
    with mock.patch(
            'greenbudget.app.user.mail.contacts_api.get_contacts_from_list') \
            as m:
        m.return_value = mock_response
        response = api_client.post("/v1/users/registration/", data={
            "first_name": "Jack",
            "last_name": "Johnson",
            "password": "hoopla@H9_12",
            "email": "jJohnson@gmail.com",
        })
    assert m.called
    assert response.status_code == 201
    assert response.json()['email'] == 'jjohnson@gmail.com'


@override_settings(WAITLIST_ENABLED=True)
def test_registration_user_not_on_waitlist(api_client):
    mock_response = mock.MagicMock()
    mock_response.contacts = []

    with mock.patch(
            'greenbudget.app.user.mail.contacts_api.get_contacts_from_list') \
            as m:
        m.return_value = mock_response
        response = api_client.post("/v1/users/registration/", data={
            "first_name": "Jack",
            "last_name": "Johnson",
            "password": "hoopla@H9_12",
            "email": "jjohnson@gmail.com",
        })
    assert m.called
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
        "billing_status": None,
        "product_id": None,
        "metrics": {
            "num_budgets": 0,
            "num_templates": 0,
            "num_collaborating_budgets": 0,
            "num_archived_budgets": 0
        }
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
        "billing_status": None,
        "product_id": None,
        "metrics": {
            "num_budgets": 0,
            "num_templates": 0,
            "num_collaborating_budgets": 0,
            "num_archived_budgets": 0
        }
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
