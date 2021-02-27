def test_login(user, api_client):
    user.set_password("testpassword123")
    user.save()
    response = api_client.post("/v1/auth/login/", data={
        "email": user.email,
        "password": "testpassword123"
    })
    assert response.status_code == 201
    assert response.json() == {'detail': 'Successfully logged in.'}
    assert 'greenbudgetjwt' in response.cookies


def test_login_missing_password(user, api_client):
    response = api_client.post("/v1/auth/login/", data={
        "email": user.email,
    })
    assert response.status_code == 400
    assert 'greenbudgetjwt' not in response.cookies


def test_login_missing_email(user, api_client):
    response = api_client.post("/v1/auth/login/", data={
        "password": user.password,
    })
    assert response.status_code == 400
    assert 'greenbudgetjwt' not in response.cookies


def test_login_invalid_email(api_client, db):
    response = api_client.post("/v1/auth/login/", data={
        "email": "userdoesnotexist@gmail.com",
        "password": "fake-password",
    })
    assert response.status_code == 403
    assert 'greenbudgetjwt' not in response.cookies
    assert response.json() == {
        'errors': {
            '__all__': [{
                'message': 'The provided username does not exist in our system.',  # noqa
                'code': 'email_does_not_exist'
            }]
        }
    }


def test_login_invalid_password(user, api_client):
    response = api_client.post("/v1/auth/login/", data={
        "email": user.email,
        "password": "fake-password",
    })
    assert response.status_code == 403
    assert 'greenbudgetjwt' not in response.cookies
    assert response.json() == {
        'errors': {
            '__all__': [{
                'message': 'The provided password is invalid.',
                'code': 'invalid_credentials'
            }]
        }
    }


def test_logout(user, api_client):
    api_client.force_login(user)
    response = api_client.post("/v1/auth/logout/")
    assert response.status_code == 201
    assert response.cookies['greenbudgetjwt'].value == ""
