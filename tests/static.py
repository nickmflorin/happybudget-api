from io import BytesIO
from PIL import Image
import pytest

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.images import ImageFile

from .factories import *  # noqa
from .models import *  # noqa
from .stripe import *  # noqa


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
def test_image_file(tmp_path):
    def inner(name, ext):
        file_obj = BytesIO()
        filename = tmp_path / name
        image = Image.new('RGB', (100, 100))
        image.save(file_obj, ext)
        file_obj.seek(0)

        # We have to actually save the File Object to the specified directory.
        with open(str(filename), 'wb') as out:
            out.write(file_obj.read())

        return ImageFile(file_obj, name=str(filename))
    return inner


@pytest.fixture
def test_uploaded_file(test_image):
    def inner(name):
        return SimpleUploadedFile(name, test_image.getvalue())
    return inner
