# pylint: disable=redefined-outer-name
from datetime import datetime
from http.cookies import SimpleCookie
from unittest import mock

import pytest

from django.http import HttpResponse
from django.utils.http import http_date

from greenbudget.app.authentication.tokens import AuthToken
import greenbudget.app.authentication.middleware
from greenbudget.app.authentication.exceptions import ExpiredToken, InvalidToken
from greenbudget.app.authentication.middleware import (
    AuthTokenCookieMiddleware, get_cookie_user)

from greenbudget.app.user.contrib import AnonymousUser


@pytest.fixture
def middleware_patch():
    def mock_patch(attr, **kwargs):
        return mock.patch.object(
            greenbudget.app.authentication.middleware, attr, **kwargs)
    return mock_patch


@pytest.fixture
def req(rf):
    def inner(method="get", **cookies):
        rf.cookies = SimpleCookie(cookies)
        request = getattr(rf, method)('/')
        return request
    return inner


@pytest.mark.parametrize("setting_name", ['JWT_TOKEN_COOKIE_NAME'])
def test_process_request_assert_settings(middleware_patch, settings, req,
        setting_name):
    delattr(settings, setting_name)

    middleware = AuthTokenCookieMiddleware()
    with middleware_patch('get_cookie_user',
            side_effect=Exception("This should not be called")):
        with pytest.raises(AssertionError, match=setting_name):
            middleware.process_request(req())


def test_process_request_get_user_called(middleware_patch, req):
    middleware = AuthTokenCookieMiddleware()
    user = AnonymousUser()
    request = req()
    with middleware_patch('get_cookie_user', return_value=user) as mock_fn:
        middleware.process_request(request)
        assert mock_fn.call_count == 0, (
            "request.cookie_user is lazy, and it should not be called.")
        # pylint: disable=pointless-statement
        request.cookie_user.is_active
        assert mock_fn.mock_calls == [mock.call(request)]
        assert request.cookie_user == user


def test_get_cookie_user_request_has_cached_user(middleware_patch, req, user):
    request = req()
    request._cached_cookie_user = user
    with middleware_patch(
            'parse_token', return_value=(None, None)) as mock_fn:
        request_user = get_cookie_user(request)
        assert user == request_user
        assert mock_fn.call_count == 0


def test_get_cookie_user_raises_expired_token(middleware_patch, rf, user):
    # The middleware will simply use the session user in the case that the
    # request is not to the validate endpoint.
    request = rf.post("/v1/auth/validate/")
    # If there isn't a session user on the request, the middleware will not
    # attempt to parse the JWT token.
    request.user = user
    with middleware_patch('parse_token', side_effect=ExpiredToken()):
        with pytest.raises(ExpiredToken):
            get_cookie_user(request)


def test_get_cookie_user_raises_invalid_token(middleware_patch, rf, user):
    # The middleware will simply use the session user in the case that the
    # request is not to the validate endpoint.
    request = rf.post("/v1/auth/validate/")
    # If there isn't a session user on the request, the middleware will not
    # attempt to parse the JWT token.
    request.user = user
    with middleware_patch('parse_token', side_effect=InvalidToken()):
        with pytest.raises(InvalidToken):
            get_cookie_user(request)


def test_get_cookie_user_passes_cookie_args(settings, middleware_patch, rf,
        user):
    rf.cookies = SimpleCookie({settings.JWT_TOKEN_COOKIE_NAME: 'token'})
    # The middleware will simply use the session user in the case that the
    # request is not to the validate endpoint.
    request = rf.post("/v1/auth/validate/")
    # If there isn't a session user on the request, the middleware will not
    # attempt to parse the JWT token.
    request.user = user
    middleware = AuthTokenCookieMiddleware()
    middleware.process_request(request)
    with middleware_patch(
            'parse_token', return_value=(AnonymousUser(), None)) as mock_fn:
        get_cookie_user(request)
    assert mock_fn.mock_calls == [mock.call('token')]


@ pytest.mark.freeze_time('2021-01-01')
def test_process_response_sets_cookies(settings, req, user):
    token = AuthToken.for_user(user)

    expire_date = datetime.now() + \
        settings.SIMPLE_JWT['SLIDING_TOKEN_REFRESH_LIFETIME']
    http_expire_date = http_date(expire_date.timestamp())

    request = req()
    request.cookie_user = user
    response = HttpResponse()
    middleware = AuthTokenCookieMiddleware()

    with mock.patch.object(AuthToken, 'for_user',
            return_value=token) as mock_for_user:
        response = middleware.process_response(request, response)
        jwt_cookie = response.cookies[settings.JWT_TOKEN_COOKIE_NAME]

        assert jwt_cookie.value == str(token)
        assert jwt_cookie['expires'] == http_expire_date

        assert mock_for_user.mock_calls == [mock.call(user)]


def test_middleware_corrupted_token_deletes_cookies(settings, req, user):
    token = AuthToken.for_user(user)
    token.set_exp(claim='refresh_exp')
    user.delete()

    middleware = AuthTokenCookieMiddleware()

    request = req(**{settings.JWT_TOKEN_COOKIE_NAME: str(token)})
    middleware.process_request(request)

    response = HttpResponse()
    response.set_cookie(settings.JWT_TOKEN_COOKIE_NAME, str(token))

    new_response = middleware.process_response(request, response)
    assert new_response.cookies[settings.JWT_TOKEN_COOKIE_NAME].value == ''


@ pytest.mark.freeze_time('2021-01-01')
def test_middleware_expired_token_deletes_cookies(settings, req, user):
    token = AuthToken.for_user(user)
    token.set_exp(claim='refresh_exp', from_time=datetime(2010, 1, 1))

    middleware = AuthTokenCookieMiddleware()

    request = req(**{settings.JWT_TOKEN_COOKIE_NAME: str(token)})
    middleware.process_request(request)

    response = HttpResponse()
    response.set_cookie(settings.JWT_TOKEN_COOKIE_NAME, str(token))

    new_response = middleware.process_response(request, response)
    assert new_response.cookies[settings.JWT_TOKEN_COOKIE_NAME].value == ''


def test_middleware_invalid_token_deletes_cookies(settings, req):
    middleware = AuthTokenCookieMiddleware()

    request = req(**{settings.JWT_TOKEN_COOKIE_NAME: 'invalid_token'})
    middleware.process_request(request)

    response = HttpResponse()
    response.set_cookie(settings.JWT_TOKEN_COOKIE_NAME, 'invalid_token')

    new_response = middleware.process_response(request, response)
    assert new_response.cookies[settings.JWT_TOKEN_COOKIE_NAME].value == ''


@ pytest.mark.parametrize("method", ['get', 'head', 'options'])
def test_middleware_doesnt_update_cookie_for_read_only_methods(
        method, middleware_patch, user, settings, req):
    middleware = AuthTokenCookieMiddleware()
    request = req(
        method=method,
        **{settings.JWT_TOKEN_COOKIE_NAME: AuthToken.for_user(user)}
    )
    response = HttpResponse()
    with mock.patch.object(response, 'set_cookie') as set_cookie:
        with middleware_patch('get_cookie_user', return_value=user):
            middleware.process_request(request)
            response = middleware.process_response(request, response)
            assert set_cookie.called is False


@pytest.mark.parametrize("method", ['post', 'patch', 'delete', 'put'])
def test_middleware_updates_cookie_for_write_methods(
        method, middleware_patch, user, settings, req):
    middleware = AuthTokenCookieMiddleware()
    request = req(
        method=method,
        **{settings.JWT_TOKEN_COOKIE_NAME: AuthToken.for_user(user)}
    )
    response = HttpResponse()
    with mock.patch.object(response, 'set_cookie') as set_cookie:
        with middleware_patch('get_cookie_user', return_value=user):
            middleware.process_request(request)
            response = middleware.process_response(request, response)

            assert set_cookie.called is True
