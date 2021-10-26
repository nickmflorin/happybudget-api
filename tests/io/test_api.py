from io import BytesIO
import mock
from PIL import Image

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from greenbudget.app.io.storages import LocalStorage


@override_settings(APP_URL="https://api.greenbudget.com")
def test_temp_upload_image(user, api_client):
    image = BytesIO()
    Image.new('RGB', (100, 100)).save(image, 'jpeg')
    image.seek(0)

    uploaded_file = SimpleUploadedFile('test.jpeg', image.getvalue())
    api_client.force_login(user)

    # Make sure to mock the .save() method so we don't actually save to the
    # file system.
    with mock.patch.object(LocalStorage, 'save') as m:
        response = api_client.post(
            "/v1/io/temp-upload-image/",
            data={"image": uploaded_file}
        )
        assert response.status_code == 200
        assert m.called
        assert response.json() == {
            'fileUrl': 'https://api.greenbudget.com/media/users/1/temp/test.jpeg'
        }


@override_settings(APP_URL="https://api.greenbudget.com")
def test_temp_upload_file(user, api_client):
    image = BytesIO()
    Image.new('RGB', (100, 100)).save(image, 'jpeg')
    image.seek(0)

    uploaded_file = SimpleUploadedFile('test.pdf', image.getvalue())
    api_client.force_login(user)

    # Make sure to mock the .save() method so we don't actually save to the
    # file system.
    with mock.patch.object(LocalStorage, 'save') as m:
        response = api_client.post(
            "/v1/io/temp-upload-file/",
            data={"file": uploaded_file}
        )
        assert response.status_code == 200
        assert m.called
        assert response.json() == {
            'fileUrl': 'https://api.greenbudget.com/media/users/1/temp/test.pdf'
        }


@override_settings(APP_URL="https://api.greenbudget.com")
def test_temp_upload_image_invalid_extension(user, api_client):
    image = BytesIO()
    Image.new('RGB', (100, 100)).save(image, 'gif')
    image.seek(0)

    uploaded_file = SimpleUploadedFile('test.gif', image.getvalue())
    api_client.force_login(user)

    # Make sure to mock the .save() method so we don't actually save to the
    # file system.
    with mock.patch.object(LocalStorage, 'save') as m:
        response = api_client.post(
            "/v1/io/temp-upload-image/",
            data={"image": uploaded_file}
        )
        assert response.status_code == 400
        assert m.called is False
        assert response.json() == {
            'errors': [{
                'message': 'The file extension `gif` is not supported.',
                'code': 'invalid_file_extension',
                'error_type': 'field',
                'field': '__all__'
            }]
        }
