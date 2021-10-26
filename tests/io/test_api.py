from django.test import override_settings


@override_settings(APP_URL="https://api.greenbudget.com")
def test_temp_upload_image(user, api_client, test_uploaded_file):
    uploaded_file = test_uploaded_file('test.jpeg')
    api_client.force_login(user)

    response = api_client.post(
        "/v1/io/temp-upload-image/",
        data={"image": uploaded_file}
    )
    assert response.status_code == 200
    assert response.json() == {
        'fileUrl': 'https://api.greenbudget.com/media/users/1/temp/test.jpeg'
    }


@override_settings(APP_URL="https://api.greenbudget.com")
def test_temp_upload_file(user, api_client, test_uploaded_file):
    uploaded_file = test_uploaded_file('test.pdf')
    api_client.force_login(user)

    response = api_client.post(
        "/v1/io/temp-upload-file/",
        data={"file": uploaded_file}
    )
    assert response.status_code == 200
    assert response.json() == {
        'fileUrl': 'https://api.greenbudget.com/media/users/1/temp/test.pdf'
    }


@override_settings(APP_URL="https://api.greenbudget.com")
def test_temp_upload_image_invalid_extension(user, api_client,
        test_uploaded_file):
    uploaded_file = test_uploaded_file('test.gif')
    api_client.force_login(user)

    response = api_client.post(
        "/v1/io/temp-upload-image/",
        data={"image": uploaded_file}
    )
    assert response.status_code == 400
    assert response.json() == {
        'errors': [{
            'message': 'The file extension `gif` is not supported.',
            'code': 'invalid_file_extension',
            'error_type': 'field',
            'field': '__all__'
        }]
    }
