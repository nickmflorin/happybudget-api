from io import BytesIO
import logging
from PIL import Image
import pytest
import requests

from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile

from rest_framework.test import APIClient

from greenbudget.app.budget.models import Budget
from greenbudget.app.fringe.models import Fringe
from greenbudget.app.group.models import Group
from greenbudget.app.tagging.models import Color
from greenbudget.app.template.models import Template
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
    caplog.set_level(logging.INFO, logger="greenbudget")


@pytest.fixture
def api_client():
    class GreenbudgetApiClient(APIClient):
        def force_login(self, user, **kwargs):
            self.force_authenticate(user)
            super().force_login(user, **kwargs)

    return GreenbudgetApiClient()


@pytest.fixture(autouse=True)
def temp_media_root(tmpdir, settings):
    settings.MEDIA_ROOT = tmpdir


@pytest.fixture
def test_image():
    image = BytesIO()
    Image.new('RGB', (100, 100)).save(image, 'jpeg')
    image.seek(0)
    return image


@pytest.fixture
def test_uploaded_file(test_image):
    def inner(name):
        return SimpleUploadedFile(name, test_image.getvalue())
    return inner


@pytest.fixture
def user_password():
    return 'hoopla@H9_145'


@pytest.fixture
def user(db, user_password):
    user = User.objects.create(
        email="test+user@gmail.com",
        first_name="Test",
        last_name="User",
        is_active=True,
        is_admin=False,
        is_staff=False,
        is_superuser=False,
        is_verified=True,
        is_first_time=False
    )
    user.set_password(user_password)
    user.save()
    return user


@pytest.fixture
def admin_user(db, user_password):
    user = User.objects.create(
        email="admin+user@gmail.com",
        first_name="Admin",
        last_name="User",
        is_active=True,
        is_admin=True,
        is_staff=False,
        is_verified=True,
        is_superuser=False,
        is_first_time=False
    )
    user.set_password(user_password)
    user.save()
    return user


@pytest.fixture
def staff_user(db, user_password):
    user = User.objects.create(
        email="staff+user@gmail.com",
        first_name="Staff",
        last_name="User",
        is_active=True,
        is_admin=False,
        is_staff=True,
        is_superuser=False,
        is_verified=True,
        is_first_time=False
    )
    user.set_password(user_password)
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


CONTEXT_BUDGETS = {
    'budget': Budget,
    'template': Template
}


@pytest.fixture(params=["budget", "template"])
def budget_f(request, create_context_budget, create_account,
        create_subaccount, create_subaccounts):
    markers = request.node.own_markers
    marker_names = [m.name for m in markers]
    if 'budget' not in marker_names and 'template' not in marker_names:
        marker_names = marker_names + ['budget', 'template']

    class BudgetFactories:
        def __init__(self, context):
            self.context = context
            self.budget_cls = CONTEXT_BUDGETS[self.context]

        def create_budget(self, *args, **kwargs):
            kwargs.setdefault('context', self.context)
            return create_context_budget(*args, **kwargs)

        def create_account(self, *args, **kwargs):
            kwargs.setdefault('context', self.context)
            return create_account(*args, **kwargs)

        def create_subaccount(self, *args, **kwargs):
            kwargs.setdefault('context', self.context)
            return create_subaccount(*args, **kwargs)

        def create_subaccounts(self, *args, **kwargs):
            kwargs.setdefault('context', self.context)
            return create_subaccounts(*args, **kwargs)

    if request.param in marker_names:
        yield BudgetFactories(request.param)
    else:
        pytest.skip("Test is not applicable for `%s` context." % request.param)
