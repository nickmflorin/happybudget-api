import pytest

from greenbudget.app.user.models import User


@pytest.mark.freeze_time('2020-01-01')
def test_registration(api_client, db):
    response = api_client.post("/v1/users/registration/", data={
        "first_name": "Jack",
        "last_name": "Johnson",
        "password": "Hoopla",
        "email": "jjohnson@gmail.com",
    })
    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "first_name": "Jack",
        "last_name": "Johnson",
        "email": "jjohnson@gmail.com",
        "username": "jjohnson@gmail.com",
        "is_active": True,
        "is_admin": False,
        "is_superuser": False,
        "is_staff": False,
        "full_name": "Jack Johnson",
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "last_login": None,
        "date_joined": "2020-01-01 00:00:00",
        "timezone": "America/New_York"
    }
    user = User.objects.get(pk=response.json()['id'])
    assert user.first_name == "Jack"
    assert user.last_name == "Johnson"
    assert user.email == "jjohnson@gmail.com"
    assert user.username == "jjohnson@gmail.com"
    assert user.is_staff is False
    assert user.is_admin is False
    assert user.is_superuser is False
    assert user.is_active is True
    assert user.check_password("Hoopla") is True
