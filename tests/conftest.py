from datetime import timedelta
from django.utils import timezone
import logging
import pytest
import requests
from rest_framework.test import APIClient


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


@pytest.fixture(autouse=True)
def disable_logging(caplog):
    """
    Disable logging behavior in certain packages.
    """
    caplog.set_level(logging.CRITICAL, logger="factory")
    caplog.set_level(logging.CRITICAL, logger="faker.factory")
    caplog.set_level(logging.CRITICAL, logger="factory-boy")


@pytest.fixture
def api_client():
    class GreenbudgetApiClient(APIClient):
        def force_login(self, user, **kwargs):
            self.force_authenticate(user)
            super().force_login(user, **kwargs)

    return GreenbudgetApiClient()
