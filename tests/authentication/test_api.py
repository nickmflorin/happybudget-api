import pytest


@pytest.fixture
def login(api_client, user_with_password, password):
    def inner(exclude=None, user_kwargs=None, **kwargs):
        if user_kwargs:
            for k, v in user_kwargs.items():
                setattr(user_with_password, k, v)
            user_with_password.save()
        exclude = exclude or []
        data = {"email": user_with_password.email, "password": password}
        data.update(**kwargs)
        data = dict((k, v) for k, v in data.items() if k not in exclude)
        return api_client.post("/v1/auth/login/", data=data)
    return inner


@pytest.mark.freeze_time('2020-01-01')
def test_login(login, user_with_password, settings):
    response = login()
    assert response.status_code == 201
    assert settings.JWT_TOKEN_COOKIE_NAME in response.cookies
    assert response.json() == {
        "id": 1,
        "first_name": user_with_password.first_name,
        "last_name": user_with_password.last_name,
        "email": user_with_password.email,
        "is_active": True,
        "is_admin": False,
        "is_superuser": False,
        "is_staff": False,
        "company": user_with_password.company,
        "position": user_with_password.position,
        "address": user_with_password.address,
        "phone_number": user_with_password.phone_number,
        "full_name": user_with_password.full_name,
        "last_login": "2020-01-01 00:00:00",
        "date_joined": "2020-01-01 00:00:00",
        "profile_image": None,
        "timezone": "America/New_York",
        "is_first_time": False,
        "stripe_product": None,
    }


def test_login_missing_password(login, settings):
    response = login(exclude=["password"])
    assert response.status_code == 400
    assert settings.JWT_TOKEN_COOKIE_NAME not in response.cookies


def test_login_missing_email(login, settings):
    response = login(exclude=["email"])
    assert response.status_code == 400
    assert settings.JWT_TOKEN_COOKIE_NAME not in response.cookies


def test_login_invalid_email(login, settings):
    response = login(email="userdoesnotexist@gmail.com")
    assert response.status_code == 400
    assert settings.JWT_TOKEN_COOKIE_NAME not in response.cookies
    assert response.json() == {
        'errors': [{
            'message': 'The provided username does not exist in our system.',  # noqa
            'error_type': 'field',
            'field': 'email',
            'code': 'email_does_not_exist'
        }]
    }


def test_login_invalid_password(login, settings):
    response = login(password="fake")
    assert response.status_code == 400
    assert settings.JWT_TOKEN_COOKIE_NAME not in response.cookies
    assert response.json() == {
        'errors': [{
            'message': 'The provided password is invalid.',
            'error_type': 'field',
            'field': 'password',
            'code': 'invalid_credentials'
        }]
    }


def test_login_account_disabled(login, settings):
    response = login(user_kwargs={'is_active': False})
    assert response.status_code == 403
    assert settings.JWT_TOKEN_COOKIE_NAME not in response.cookies
    assert response.json() == {
        'user_id': 1,
        'errors': [{
            'message': 'Your account is not active, please contact customer care.',  # noqa
            'code': 'account_disabled',
            'error_type': 'auth'
        }]
    }


def test_login_account_not_approved(login, settings):
    response = login(user_kwargs={'is_approved': False})
    assert response.status_code == 403
    assert settings.JWT_TOKEN_COOKIE_NAME not in response.cookies
    assert response.json() == {
        'user_id': 1,
        'errors': [{
            'message': 'The account is not approved.',
            'code': 'account_not_approved',
            'error_type': 'auth'
        }]
    }


def test_login_account_not_verified(login, settings):
    response = login(user_kwargs={'is_verified': False})
    assert response.status_code == 403
    assert settings.JWT_TOKEN_COOKIE_NAME not in response.cookies
    assert response.json() == {
        'user_id': 1,
        'errors': [{
            'message': 'The email address is not verified.',
            'code': 'account_not_verified',
            'error_type': 'auth'
        }]
    }


def test_logout(user, jwt_authenticated_client, settings):
    jwt_authenticated_client.force_login(user)
    response = jwt_authenticated_client.post("/v1/auth/logout/")
    assert response.status_code == 201
    assert response.cookies[settings.JWT_TOKEN_COOKIE_NAME].value == ""
