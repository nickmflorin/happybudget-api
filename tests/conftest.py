import logging
import pytest
import requests

from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient

from greenbudget.app.fringe.models import Fringe
from greenbudget.app.group.models import Group
from greenbudget.app.tagging.models import Color
from greenbudget.app.user.models import User

from .fixtures import *  # noqa


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


@pytest.fixture
def user(db):
    user = User.objects.create(
        email="test+user@gmail.com",
        username="test+user@gmail.com",
        first_name="Test",
        last_name="User",
        is_active=True,
        is_admin=False,
        is_staff=False,
        is_superuser=False,
    )
    user.set_password("test-password")
    user.save()
    return user


@pytest.fixture
def admin_user(db):
    user = User.objects.create(
        email="admin+user@gmail.com",
        username="admin+user@gmail.com",
        first_name="Admin",
        last_name="User",
        is_active=True,
        is_admin=True,
        is_staff=False,
        is_superuser=False,
    )
    user.set_password("test-password")
    user.save()
    return user


@pytest.fixture
def staff_user(db):
    user = User.objects.create(
        email="staff+user@gmail.com",
        username="staff+user@gmail.com",
        first_name="Staff",
        last_name="User",
        is_active=True,
        is_admin=False,
        is_staff=True,
        is_superuser=False,
    )
    user.set_password("test-password")
    user.save()
    return user


@pytest.fixture
def login_user(api_client, user):
    api_client.force_login(user)


@pytest.fixture(autouse=True)
def colors(db):
    color_list = ['#a1887f', '#EFEFEF']
    content_types = [
        ContentType.objects.get_for_model(m) for m in [Group, Fringe]
    ]
    colors = []
    for i, code in enumerate(color_list):
        color_obj = Color.objects.create(code=code, name="Test Color %s" % i)
        color_obj.content_types.set(content_types)
        color_obj.save()
        colors.append(color_obj)
    yield colors
