import pytest

from django.contrib.auth.models import AnonymousUser
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from greenbudget.app.authentication import exceptions
from greenbudget.app.authentication.backends import (
    SessionAuthentication, CookieSessionAuthentication)


class FixedAPIRequestFactory(APIRequestFactory):
    def request(self, **kwargs):
        return Request(super().request(**kwargs))


@pytest.fixture
def api_rf():
    return FixedAPIRequestFactory()


def test_session_authenticate_successful(api_rf, user):
    backend = SessionAuthentication()
    request = api_rf.get('/')
    request._request.user = user

    auth_user = backend.authenticate(request)
    assert isinstance(auth_user, tuple), "Authentication unsuccessful."
    assert auth_user[0].pk == user.pk


@pytest.mark.parametrize("unauthorized_user", [None, AnonymousUser()])
def test_session_failure_unauthenticated_user(api_rf, unauthorized_user):
    request = api_rf.get('/')
    request._request.user = unauthorized_user
    backend = SessionAuthentication()
    with pytest.raises(exceptions.NotAuthenticatedError):
        backend.authenticate(request)


def test_session_failure_inactive_user(api_rf, user):
    user.is_active = False
    user.save()
    request = api_rf.get('/')
    request._request.user = user
    backend = SessionAuthentication()
    with pytest.raises(exceptions.AccountDisabledError):
        backend.authenticate(request)


def test_session_failure_unverified_user(api_rf, user):
    user.is_verified = False
    user.save()
    request = api_rf.get('/')
    request._request.user = user
    backend = SessionAuthentication()
    with pytest.raises(exceptions.EmailNotVerified):
        backend.authenticate(request)


def test_cookie_session_authenticate_successful(api_rf, user):
    backend = CookieSessionAuthentication()
    request = api_rf.get('/')
    request._request.cookie_user = user

    auth_user = backend.authenticate(request)
    assert isinstance(auth_user, tuple), "Authentication unsuccessful."
    assert auth_user[0].pk == user.pk


@pytest.mark.parametrize("unauthorized_user", [None, AnonymousUser()])
def test_cookie_session_failure_unauthenticated_user(api_rf, unauthorized_user):
    request = api_rf.get('/')
    request._request.cookie_user = unauthorized_user
    backend = CookieSessionAuthentication()
    with pytest.raises(exceptions.NotAuthenticatedError):
        backend.authenticate(request)


def test_cookie_session_failure_inactive_user(api_rf, user):
    user.is_active = False
    user.save()
    request = api_rf.get('/')
    request._request.cookie_user = user
    backend = CookieSessionAuthentication()
    with pytest.raises(exceptions.AccountDisabledError):
        backend.authenticate(request)


def test_cookie_session_failure_unverified_user(api_rf, user):
    user.is_verified = False
    user.save()
    request = api_rf.get('/')
    request._request.cookie_user = user
    backend = CookieSessionAuthentication()
    with pytest.raises(exceptions.EmailNotVerified):
        backend.authenticate(request)
