import pytest


@pytest.mark.parametrize("password", [
    'hoopla',  # Not 8 characters long
    'hoopla122412H',  # No special characters
    'hoopla@JJ',  # No numbers
    'hoopla123@',  # No capital letters
])
def test_registration_invalid_password(api_client, password):
    response = api_client.post("/v1/users/registration/", data={
        "first_name": "Jack",
        "last_name": "Johnson",
        "password": password,
        "email": "jjohnson@gmail.com",
    })
    assert response.status_code == 400
    assert response.json()['errors'][0]['field'] == 'password'
    assert response.json()['errors'][0]['code'] == 'invalid_password'


@pytest.mark.freeze_time('2020-01-01')
def test_registration(api_client, models):
    response = api_client.post("/v1/users/registration/", data={
        "first_name": "Jack",
        "last_name": "Johnson",
        "password": "hoopla@H9_12",
        "email": "jjohnson@gmail.com",
    })
    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "first_name": "Jack",
        "last_name": "Johnson",
        "email": "jjohnson@gmail.com",
        "is_active": True,
        "is_admin": False,
        "is_superuser": False,
        "is_staff": False,
        "company": None,
        "position": None,
        "address": None,
        "phone_number": None,
        "full_name": "Jack Johnson",
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "last_login": "2020-01-01 00:00:00",
        "date_joined": "2020-01-01 00:00:00",
        "profile_image": None,
        "timezone": "America/New_York",
        "is_first_time": True,
    }
    user = models.User.objects.get(pk=response.json()['id'])
    assert user.first_name == "Jack"
    assert user.last_name == "Johnson"
    assert user.email == "jjohnson@gmail.com"
    assert user.is_staff is False
    assert user.is_admin is False
    assert user.is_superuser is False
    assert user.is_active is True
    assert user.check_password("hoopla@H9_12") is True

    # The user should be saved as not being first time anymore, but the response
    # should indicate that it was their first time logging in.
    assert user.is_first_time is False


@pytest.mark.freeze_time('2020-01-01')
def test_update_logged_in_user(api_client, user):
    api_client.force_login(user)
    response = api_client.patch("/v1/users/user/", data={
        'first_name': 'New First Name',
        'last_name': 'New Last Name'
    })
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "first_name": "New First Name",
        "last_name": "New Last Name",
        "email": user.email,
        "is_active": True,
        "is_admin": False,
        "is_superuser": False,
        "is_staff": False,
        "company": user.company,
        "position": user.position,
        "address": user.address,
        "phone_number": user.phone_number,
        "full_name": "New First Name New Last Name",
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "last_login": "2020-01-01 00:00:00",
        "date_joined": "2020-01-01 00:00:00",
        "profile_image": None,
        "timezone": str(user.timezone),
        "is_first_time": False,
    }

    user.refresh_from_db()
    assert user.first_name == "New First Name"
    assert user.last_name == "New Last Name"


@pytest.mark.freeze_time('2020-01-01')
def test_change_password(api_client, user):
    api_client.force_login(user)
    response = api_client.patch("/v1/users/change-password/", data={
        "password": "hoopla@H9_12",
    })
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "is_active": True,
        "is_admin": False,
        "is_superuser": False,
        "is_staff": False,
        "company": user.company,
        "position": user.position,
        "address": user.address,
        "phone_number": user.phone_number,
        "full_name": user.full_name,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "last_login": "2020-01-01 00:00:00",
        "date_joined": "2020-01-01 00:00:00",
        "profile_image": None,
        "timezone": str(user.timezone),
        "is_first_time": False,
    }

    user.refresh_from_db()
    assert user.check_password("hoopla@H9_12")


@pytest.mark.parametrize("password", [
    'hoopla',  # Not 8 characters long
    'hoopla122412H',  # No special characters
    'hoopla@JJ',  # No numbers
    'hoopla123@',  # No capital letters
])
def test_change_password_invalid_password(api_client, password, user):
    api_client.force_login(user)
    response = api_client.patch("/v1/users/change-password/", data={
        "password": password,
    })
    assert response.status_code == 400
    assert response.json()['errors'][0]['field'] == 'password'
    assert response.json()['errors'][0]['code'] == 'invalid_password'
