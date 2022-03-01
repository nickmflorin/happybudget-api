import copy
import functools
import mock
import pytest
import requests
import threading
import time

from django.core.cache import cache as django_cache
from django.db import connection, connections

from rest_framework.test import APIClient

from greenbudget.app import cache
from greenbudget.app.authentication.models import PublicToken

from .factories import *  # noqa
from .models import *  # noqa
from .stripe import *  # noqa


VALID_CACHE_BACKEND = 'django.core.cache.backends.db.DatabaseCache'


@pytest.fixture(autouse=True)
def no_requests(monkeypatch):
    """
    Prevent any requests from actually executing.
    """
    original_session_request = requests.sessions.Session.request

    def failing_request(*args, **kwargs):
        # The responses package is used for mocking responses down the the most
        # granular level.  If this package is enabled, we do not want to raise
        # an Exception because the mocking itself prevents the HTTP request.
        if requests.adapters.HTTPAdapter.send.__qualname__.startswith(
                'RequestsMock'):
            return original_session_request(*args, **kwargs)
        else:
            raise Exception("No network access allowed in tests")

    monkeypatch.setattr('requests.sessions.Session.request', failing_request)
    monkeypatch.setattr(
        'requests.sessions.HTTPAdapter.send', failing_request)


@pytest.fixture
def api_client(settings):
    class GreenbudgetApiClient(APIClient):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._dynamic_headers = {}

        def force_login(self, user, **kwargs):
            self.force_authenticate(user)
            super().force_login(user, **kwargs)

        def generic(self, *args, **kwargs):
            kwargs_with_headers = copy.deepcopy(self._dynamic_headers)
            if self._dynamic_headers:
                # Headers provided on request should always override those set
                # dynamically on the client.
                kwargs_with_headers.update(**kwargs)
            return super().generic(*args, **kwargs_with_headers)

        def include_public_token(self, token):
            header_name = (
                settings.PUBLIC_TOKEN_HEADER.replace('-', '_').upper())
            if isinstance(token, PublicToken):
                self._dynamic_headers[header_name] = str(token.private_id)
            else:
                self._dynamic_headers[header_name] = str(token)

    return GreenbudgetApiClient()


@pytest.fixture
def login_user(api_client, user):
    api_client.force_login(user)


@pytest.fixture
def test_concurrently():
    """
    Fixture that returns a decorator such that when a function is decorated
    with the returned decorator, the function will execute `count` number of
    times concurrently.
    """
    def inner(count, sleep=None):
        def decorator(func):
            @functools.wraps(func)
            def inner(*args, **kwargs):
                exceptions = []
                results = [None for _ in range(count)]

                def call_func(i):
                    try:
                        result = func(*args, **kwargs)
                    except Exception as e:
                        exceptions.append(e)
                        raise e
                    else:
                        results[i] = result

                threads = []
                for i in range(count):
                    threads.append(threading.Thread(
                        target=call_func, args=(i, )))
                for t in threads:
                    t.start()
                    if sleep:
                        time.sleep(sleep)
                for t in threads:
                    t.join()

                # TODO: We may need to remove this at some point.
                connections.close_all()

                if exceptions:
                    stringified = "\n".join([str(e) for e in exceptions])
                    raise Exception(
                        f"Concurrent test intercepted {len(exceptions)} "
                        f"exceptions: {stringified}"
                    )
                return results
            return inner
        return decorator
    return inner


@pytest.fixture(autouse=True)
def validate_cache():
    return cache.is_engine(
        engine=VALID_CACHE_BACKEND,
        strict=True
    )


@pytest.fixture(autouse=True)
def mock_cache_pattern_deletion(settings, monkeypatch):
    cache.is_engine(engine=VALID_CACHE_BACKEND, strict=True)
    cache_table = settings.CACHES['default']['LOCATION']
    original_invalidate = cache.endpoint_cache._invalidate

    def mock_invalidate(instance, key):
        if key.key.endswith('*'):
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM %s WHERE cache_key LIKE '%s'"
                    % (cache_table,
                        django_cache.make_key(key.key.replace('*', '%')))
                )
            return
        original_invalidate(instance, key)

    monkeypatch.setattr(cache.endpoint_cache, '_invalidate', mock_invalidate)


@pytest.fixture
def establish_cache_user():
    mock_request = mock.MagicMock()

    def establish(user):
        mock_request.user = user
        cache.endpoint_cache.thread.request = mock_request
    return establish
