# pylint: disable=redefined-outer-name
import pytest

import django.apps
from django.contrib.contenttypes.models import ContentType

from greenbudget.app.fringe.models import Fringe
from greenbudget.app.group.models import Group
from greenbudget.app.tagging.models import Color
from greenbudget.app.user.models import User


@pytest.fixture
def models(db):
    class Models:
        def __init__(self):
            for model in django.apps.apps.get_models():
                setattr(self, model.__name__, model)
    return Models()


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
        is_staff=True,
        is_superuser=False,
        is_verified=True,
        is_first_time=False
    )
    user.set_password(user_password)
    user.save()
    return user


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
