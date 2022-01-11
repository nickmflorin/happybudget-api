import pytest
import responses

from django.test import override_settings


@responses.activate
@pytest.mark.freeze_time('2020-01-01')
@override_settings(GOOGLE_OAUTH_API_URL="https://www.test-validate-user-token/")
def test_social_login_user_exists(api_client, create_user):
    # A user with an unverified email should still be able to do social login
    # and their email address should be considered verified afterwards.
    user = create_user(email="jjohnson@gmail.com", is_verified=False)
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

    assert 'greenbudgetjwt' in response.cookies
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
        "timezone": "America/New_York",
        "is_first_time": False,
        "product_id": None,
        "billing_status": None
    }


@responses.activate
@pytest.mark.freeze_time('2020-01-01')
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
    assert user.is_verified

    assert response.status_code == 201
    assert 'greenbudgetjwt' in response.cookies
    assert response.json() == {
        "id": 1,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "is_active": True,
        "is_admin": False,
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
        "billing_status": None
    }


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
    assert response.status_code == 403
    assert 'greenbudgetjwt' not in response.cookies


@responses.activate
@override_settings(GOOGLE_OAUTH_API_URL="https://www.test-validate-user-token/")
def test_social_login_invalid_provider(api_client, create_user):
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


@responses.activate
@override_settings(GOOGLE_OAUTH_API_URL="https://www.test-validate-user-token/")
def test_social_login_account_disabled(api_client, create_user):
    user = create_user(email="jjohnson@gmail.com", is_active=False)
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
    assert 'greenbudgetjwt' not in response.cookies
    assert response.json() == {
        'errors': [{
            'message': 'The account is not active.',
            'code': 'account_disabled',
            'error_type': 'auth',
            'user_id': user.pk,
        }]
    }
