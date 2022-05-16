# pylint: disable=redefined-outer-name
from io import BytesIO
from PIL import Image
import pytest

from django.core.files.uploadedfile import SimpleUploadedFile

from .factories import *  # noqa
from .models import *  # noqa
from .stripe import *  # noqa


@pytest.fixture(autouse=True)
def temp_media_root(tmpdir, settings):
    settings.MEDIA_ROOT = tmpdir


@pytest.fixture
def create_image():
    def inner(ext, file_obj=None):
        file_obj = file_obj or BytesIO()
        image = Image.new('RGB', (100, 100))
        image.save(file_obj, ext)
        image.seek(0)
        return file_obj
    return inner


@pytest.fixture
def test_image(create_image):
    return create_image("jpeg")


@pytest.fixture
def test_uploaded_file(test_image):
    def inner(name):
        return SimpleUploadedFile(name, test_image.getvalue())
    return inner
