# pylint: disable=redefined-outer-name
import pytest

import django.apps
from django.contrib.contenttypes.models import ContentType


@pytest.fixture(scope='session')
def models():
    class Models:
        def __init__(self):
            for model in django.apps.apps.get_models():
                setattr(self, model.__name__, model)
    return Models()


@pytest.fixture
def user_password():
    return 'hoopla@H9_145'


@pytest.fixture
def user(db, user_password, models):
    return models.User.objects.create(
        email="test+user@gmail.com",
        first_name="Test",
        last_name="User",
        is_active=True,
        is_staff=False,
        is_superuser=False,
        is_verified=True,
        is_first_time=False,
        password=user_password
    )


@pytest.fixture
def admin_user(db, user_password, models):
    return models.User.objects.create(
        email="admin+user@gmail.com",
        first_name="Admin",
        last_name="User",
        is_active=True,
        is_staff=False,
        is_verified=True,
        is_superuser=False,
        is_first_time=False,
        password=user_password
    )


@pytest.fixture
def staff_user(db, user_password, models):
    return models.User.objects.create(
        email="staff+user@gmail.com",
        first_name="Staff",
        last_name="User",
        is_active=True,
        is_staff=True,
        is_superuser=False,
        is_verified=True,
        is_first_time=False,
        password=user_password
    )


@pytest.fixture(autouse=True)
def colors(db, models):
    color_list = ['#a1887f', '#EFEFEF']
    content_types = [
        ContentType.objects.get_for_model(m) for m in [
            models.Group, models.Fringe]
    ]
    colors = []
    for i, code in enumerate(color_list):
        color_obj = models.Color.objects.create(
            code=code,
            name=f"Test Color {i}"
        )
        color_obj.content_types.set(content_types)
        color_obj.save()
        colors.append(color_obj)
    yield colors
