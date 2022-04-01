# pylint: disable=redefined-outer-name
import pytest

from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from greenbudget.app.authentication.backends import (
    SessionAuthentication, CookieSessionAuthentication)
from greenbudget.app.user.contrib import AnonymousUser


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
    auth_user = backend.authenticate(request)
    assert auth_user is None, "Authentication successful."


def test_session_failure_inactive_user(api_rf, user):
    user.is_active = False
    user.save()
    request = api_rf.get('/')
    request._request.user = user
    backend = SessionAuthentication()
    auth_user = backend.authenticate(request)
    assert auth_user is None, "Authentication successful."


def test_session_failure_unverified_user(api_rf, user):
    user.is_verified = False
    user.save()
    request = api_rf.get('/')
    request._request.user = user
    backend = SessionAuthentication()
    auth_user = backend.authenticate(request)
    assert auth_user is None, "Authentication successful."


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
    auth_user = backend.authenticate(request)
    assert auth_user is None, "Authentication successful."


@pytest.mark.parametrize("flag", ['is_active', 'is_verified'])
def test_cookie_session_failure(api_rf, user, flag):
    setattr(user, flag, False)
    user.save()
    request = api_rf.get('/')
    request._request.cookie_user = user
    backend = CookieSessionAuthentication()
    auth_user = backend.authenticate(request)
    assert auth_user is None, \
        "Authentication unexpectedly successful for %s = False." % flag
