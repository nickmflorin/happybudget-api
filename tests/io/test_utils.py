import pytest

from greenbudget.app.io.exceptions import (
    FileNameError,
    MissingFileExtension,
    UnsupportedFileExtension
)
from greenbudget.app.io.utils import (
    upload_user_image_to,
    upload_temp_user_image_to,
    upload_user_file_to,
    upload_temp_user_file_to,
    parse_filename,
    parse_image_filename,
)


@pytest.mark.parametrize('filename,expected_filename,expected_ext', [
    ('testfile.jpg', 'testfile.jpg', 'jpg'),
    ('testFile.docx', 'testfile.docx', 'docx'),
    ('test file.pdf', 'testfile.pdf', 'pdf'),
    ('testfile', MissingFileExtension, None),
    ('testimage.', MissingFileExtension, None),
    ('test.image.gif', FileNameError, None)
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
    ('testfile', MissingFileExtension, None),
    ('testimage.', MissingFileExtension, None),
    ('test.image.gif', FileNameError, None),
    ('test.gif', UnsupportedFileExtension, None)
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


@pytest.mark.parametrize('filename,directory,expected', [
    ('SavedFile.jpg', 'd', 'users/1/temp/d/savedfile.jpg'),
    ('Saved File.jpg', 'd', 'users/1/temp/d/savedfile.jpg'),
    ('test.jpg', None, 'users/1/temp/test.jpg')
])
def test_upload_temp_user_image_to(user, filename, directory,
        expected):
    assert upload_temp_user_image_to(
        user,
        filename,
        directory=directory
    ) == expected


@pytest.mark.parametrize('filename,directory,expected', [
    ('SavedFile.jpg', 'd', 'users/1/d/savedfile.jpg'),
    ('saved file.jpg', 'd', 'users/1/d/savedfile.jpg'),
    ('savedfile.jpg', None, 'users/1/savedfile.jpg')
])
def test_upload_user_image_to(user, filename, directory, expected):
    assert upload_user_image_to(
        user,
        filename,
        directory=directory
    ) == expected


@pytest.mark.parametrize('filename,directory,expected', [
    ('SavedFile.pdf', 'd', 'users/1/temp/d/savedfile.pdf'),
    ('Saved File.pdf', 'd', 'users/1/temp/d/savedfile.pdf'),
    ('test.pdf', None, 'users/1/temp/test.pdf')
])
def test_upload_temp_user_file_to(user, filename, directory,
        expected):
    assert upload_temp_user_file_to(
        user,
        filename,
        directory=directory
    ) == expected


@pytest.mark.parametrize('filename,directory,expected', [
    ('SavedFile.pdf', 'd', 'users/1/d/savedfile.pdf'),
    ('saved file.pdf', 'd', 'users/1/d/savedfile.pdf'),
    ('savedfile.pdf', None, 'users/1/savedfile.pdf')
])
def test_upload_user_file_to(user, filename, directory, expected):
    assert upload_user_file_to(
        user,
        filename,
        directory=directory
    ) == expected
