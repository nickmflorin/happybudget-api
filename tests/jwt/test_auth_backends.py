import pytest

from django.contrib.auth.models import AnonymousUser
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from greenbudget.app.jwt.auth_backends import JWTCookieAuthentication


class FixedAPIRequestFactory(APIRequestFactory):
    def request(self, **kwargs):
        return Request(super().request(**kwargs))


@pytest.fixture
def api_rf():
    return FixedAPIRequestFactory()


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_authenticate_successful(settings, api_rf, user):
    backend = JWTCookieAuthentication()
    request = api_rf.get('/')
    request._request.cookie_user = user

    auth_user, _ = backend.authenticate(request)
    assert auth_user.pk == user.pk


@pytest.mark.parametrize("unauthorized_user", [None, AnonymousUser()])
def test_failure_unauthenticated_user(settings, api_rf, unauthorized_user):
    request = api_rf.get('/')
    request._request.cookie_user = unauthorized_user
    backend = JWTCookieAuthentication()
    auth_user = backend.authenticate(request)
    assert auth_user is None
