from http.cookies import SimpleCookie
import pytest

from greenbudget.app.authentication.tokens import AuthToken


@pytest.fixture
def password():
    return "hoopla@H9_12"


@pytest.fixture
def user_with_password(user, password):
    user.set_password(password)
    user.save()
    return user


@pytest.fixture
def inactive_user(user):
    user.is_active = False
    user.save()
    return user


@pytest.fixture
def unverified_user(user):
    user.is_verified = False
    user.save()
    return user


@pytest.fixture
def unapproved_user(user):
    user.is_approved = False
    user.save()
    return user


@pytest.fixture
def jwt_authenticated_client(api_client, settings, user):
    token = AuthToken.for_user(user)
    api_client.cookies = SimpleCookie({
        settings.JWT_TOKEN_COOKIE_NAME: str(token),
    })
    return api_client
