import mock
import pytest
import responses

from django.test import override_settings

from happybudget.conf.settings.base import SOCIAL_AUTHENTICATION_ENABLED


@responses.activate
@pytest.mark.freeze_time('2020-01-01')
@override_settings(
    GOOGLE_OAUTH_API_URL="https://www.test-validate-user-token/",
    SOCIAL_AUTHENTICATION_ENABLED=True
)
def test_social_login_user_exists(api_client, f):
    # A user with an unverified email should still be able to do social login
    # and their email address should be considered verified afterwards.
    user = f.create_user(email="jjohnson@gmail.com", is_verified=False)
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

    user.refresh_from_db()
    assert user.is_verified

    assert 'happybudgetjwt' in response.cookies
    assert response.json() == {
        "id": user.pk,
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
        "timezone": "America/New_York",
        "is_first_time": False,
        "product_id": None,
        "billing_status": None,
        "metrics": {
            "num_budgets": 0,
            "num_templates": 0,
            "num_collaborating_budgets": 0,
            "num_archived_budgets": 0
        }
    }


@responses.activate
@pytest.mark.freeze_time('2020-01-01')
@override_settings(
    GOOGLE_OAUTH_API_URL="https://www.test-validate-user-token/",
    SOCIAL_AUTHENTICATION_ENABLED=True
)
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
    assert user.is_verified

    assert response.status_code == 201
    assert 'happybudgetjwt' in response.cookies
    assert response.json() == {
        "id": 1,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "is_active": True,
        "is_superuser": False,
        "is_staff": False,
        "full_name": user.full_name,
        "company": user.company,
        "position": user.position,
        "address": user.address,
        "phone_number": user.phone_number,
        "last_login": "2020-01-01 00:00:00",
        "date_joined": "2020-01-01 00:00:00",
        "profile_image": None,
        "timezone": "America/New_York",
        "is_first_time": True,
        "product_id": None,
        "billing_status": None,
        "metrics": {
            "num_budgets": 0,
            "num_templates": 0,
            "num_collaborating_budgets": 0,
            "num_archived_budgets": 0
        }
    }


@responses.activate
@override_settings(
    GOOGLE_OAUTH_API_URL="https://www.test-validate-user-token/",
    SOCIAL_AUTHENTICATION_ENABLED=True
)
def test_social_login_invalid_token(api_client, f):
    f.create_user(email="jjohnson@gmail.com")
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
    assert response.status_code == 403
    assert 'happybudgetjwt' not in response.cookies


@responses.activate
@override_settings(
    GOOGLE_OAUTH_API_URL="https://www.test-validate-user-token/",
    SOCIAL_AUTHENTICATION_ENABLED=True
)
def test_social_login_invalid_provider(api_client, f):
    f.create_user(email="jjohnson@gmail.com")
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
    assert 'happybudgetjwt' not in response.cookies


@responses.activate
@override_settings(
    GOOGLE_OAUTH_API_URL="https://www.test-validate-user-token/",
    SOCIAL_AUTHENTICATION_ENABLED=True
)
def test_social_login_account_disabled(api_client, f):
    user = f.create_user(email="jjohnson@gmail.com", is_active=False)
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
    assert response.status_code == 403
    assert 'happybudgetjwt' not in response.cookies
    assert response.json() == {
        'errors': [{
            'message': 'The account is not active.',
            'code': 'account_disabled',
            'error_type': 'auth',
            'user_id': user.pk,
        }]
    }


@responses.activate
@override_settings(
    GOOGLE_OAUTH_API_URL="https://www.test-validate-user-token/",
    WAITLIST_ENABLED=True,
    SOCIAL_AUTHENTICATION_ENABLED=True
)
def test_social_login_user_not_on_waitlist(api_client):
    mock_response = mock.MagicMock()
    mock_response.contacts = []
    mock_response.count = 0

    responses.add(
        method=responses.GET,
        url="https://www.test-validate-user-token/?id_token=testtoken",
        json={
            "family_name": "Johnson",
            "given_name": "Jack",
            "email": "jjohnson@gmail.com"
        }
    )
    with mock.patch(
        'happybudget.app.user.mail.contacts_api.get_contacts_from_list'
    ) as m:
        m.return_value = mock_response
        response = api_client.post("/v1/auth/social-login/", data={
            "token_id": "testtoken",
            'provider': 'google',
        })
    assert m.called
    assert response.json() == {
        'errors': [{
            'message': 'The email address is not on the waitlist.',
            'code': 'account_not_on_waitlist',
            'error_type': 'auth'
        }]
    }
