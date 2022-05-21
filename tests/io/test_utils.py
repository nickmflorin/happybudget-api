import pytest

from happybudget.app.io.exceptions import (
    MissingFileExtensionError, UnsupporedFileExtensionError)
from happybudget.app.io.utils import parse_filename, parse_image_filename


@pytest.mark.parametrize('filename,expected_filename,expected_ext', [
    ('testfile.jpg', 'testfile.jpg', 'jpg'),
    ('testFile.docx', 'testfile.docx', 'docx'),
    ('test file.pdf', 'testfile.pdf', 'pdf'),
    ('testfile', MissingFileExtensionError, None),
    ('testimage.', MissingFileExtensionError, None),
])
def test_parse_filename(filename, expected_filename, expected_ext):
    if isinstance(expected_filename, type):
        with pytest.raises(expected_filename):
            parse_filename(filename)
    else:
        assert parse_filename(filename) == (
            expected_filename,
            expected_ext
        )


@pytest.mark.parametrize('filename,expected_filename,expected_ext', [
    ('testfile.jpg', 'testfile.jpg', 'jpg'),
    ('testFile.jpg', 'testfile.jpg', 'jpg'),
    ('test file.jpeg', 'testfile.jpeg', 'jpeg'),
    ('testfile', MissingFileExtensionError, None),
    ('testimage.', MissingFileExtensionError, None),
    ('test.gif', UnsupporedFileExtensionError, None)
])
def test_parse_image_filename(filename, expected_filename, expected_ext):
    if isinstance(expected_filename, type):
        with pytest.raises(expected_filename):
            parse_image_filename(filename)
    else:
        assert parse_image_filename(filename) == (
            expected_filename,
            expected_ext
        )
