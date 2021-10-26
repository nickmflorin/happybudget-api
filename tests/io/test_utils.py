import pytest

from greenbudget.app.io.exceptions import (
    FileNameError,
    FileExtensionError,
    MissingFileExtension,
    UnsupportedFileExtension
)
from greenbudget.app.io.utils import (
    upload_user_image_to,
    upload_temp_user_image_to,
    upload_user_file_to,
    upload_temp_user_file_to,
    get_image_filename_extension,
    get_filename_extension,
    get_image_filename,
    get_filename
)


@pytest.mark.parametrize('filename,expected,strict', [
    ('testfile.jpg', 'jpg', False),
    ('testfile.docx', 'docx', False),
    ('testfile.pdf', 'pdf', False),
    ('testfile', MissingFileExtension, True),
    ('testimage.', MissingFileExtension, True),
    ('test.image.gif', FileNameError, True),
    ('testfile', None, False),
    ('testfile.', None, False),
    ('testfile.gif', 'gif', False),
])
def test_get_filename_extension(filename, expected, strict):
    if isinstance(expected, type):
        with pytest.raises(expected):
            get_filename_extension(filename, strict=strict)
    else:
        assert get_filename_extension(filename, strict=strict) == expected


@pytest.mark.parametrize('filename,expected,strict', [
    ('testimage.jpg', 'jpg', False),
    ('testimage.png', 'png', False),
    ('testimage.jpeg', 'jpeg', False),
    ('testimage', MissingFileExtension, True),
    ('testimage.', MissingFileExtension, True),
    ('testimage.gif', UnsupportedFileExtension, True),
    ('test.image.gif', FileNameError, True),
    ('testimage', None, False),
    ('testimage.', None, False),
    ('testimage.gif', None, False),
])
def test_get_image_filename_extension(filename, expected, strict):
    if isinstance(expected, type):
        with pytest.raises(expected):
            get_image_filename_extension(filename, strict=strict)
    else:
        assert get_image_filename_extension(filename, strict=strict) == expected


@pytest.mark.parametrize('filename,expected,new_name', [
    ('testimage.jpg', 'newtestimage.jpg', 'newtestimage'),
    ('testimage.png', 'newtestimage.png', 'newtestimage'),
    ('testimage.jpg', FileExtensionError, 'newtestimage.png'),
    ('testimage.jpg.jpg', FileNameError, 'newtestimage.png'),
    ('testimage', MissingFileExtension, None),
    ('testimage', MissingFileExtension, 'newtestimage.png'),
    ('testimage.', MissingFileExtension, None),
    ('testimage.gif', UnsupportedFileExtension, None),
])
def test_get_image_filename(filename, expected, new_name):
    if isinstance(expected, type):
        with pytest.raises(expected):
            get_image_filename(filename, new_filename=new_name)
    else:
        assert get_image_filename(filename, new_filename=new_name) == expected


@pytest.mark.parametrize('filename,expected,new_name', [
    ('testfile.pdf', 'newtestfile.pdf', 'newtestfile'),
    ('testfile.png', 'newtestfile.png', 'newtestfile'),
    ('testfile.docx', FileExtensionError, 'newtestfile.pdf'),
    ('testfile', MissingFileExtension, None),
    ('testfile', MissingFileExtension, 'newtestfile.png'),
    ('testfile.', MissingFileExtension, None),
    ('testfile.gif', 'testfile.gif', None),
])
def test_get_filename(filename, expected, new_name):
    if isinstance(expected, type):
        with pytest.raises(expected):
            get_filename(filename, new_filename=new_name)
    else:
        assert get_filename(filename, new_filename=new_name) == expected


@pytest.mark.parametrize('filename,new_filename,directory,expected', [
    ('test.jpg', 'SavedFile', 'd', 'users/1/temp/d/savedfile.jpg'),
    ('test.jpg', 'saved file.jpg', 'd', 'users/1/temp/d/savedfile.jpg'),
    ('test.jpg', 'SavedFile', None, 'users/1/temp/savedfile.jpg'),
    ('test.jpg', None, None, 'users/1/temp/test.jpg')
])
def test_upload_temp_user_image_to(user, filename, new_filename, directory,
        expected):
    assert upload_temp_user_image_to(
        user,
        filename,
        new_filename=new_filename,
        directory=directory
    ) == expected


@pytest.mark.parametrize('filename,new_filename,directory,expected', [
    ('test.jpg', 'SavedFile', 'd', 'users/1/d/savedfile.jpg'),
    ('test.jpg', 'saved file.jpg', 'd', 'users/1/d/savedfile.jpg'),
    ('test.jpg', 'SavedFile', None, 'users/1/savedfile.jpg'),
    ('test.jpg', None, None, 'users/1/test.jpg')
])
def test_upload_user_image_to(user, filename, new_filename, directory, expected):
    assert upload_user_image_to(
        user,
        filename,
        new_filename=new_filename,
        directory=directory
    ) == expected


@pytest.mark.parametrize('filename,new_filename,directory,expected', [
    ('test.pdf', 'SavedFile', 'd', 'users/1/temp/d/savedfile.pdf'),
    ('test.pdf', 'saved file.pdf', 'd', 'users/1/temp/d/savedfile.pdf'),
    ('test.pdf', 'SavedFile', None, 'users/1/temp/savedfile.pdf'),
    ('test.pdf', None, None, 'users/1/temp/test.pdf')
])
def test_upload_temp_user_file_to(user, filename, new_filename, directory,
        expected):
    assert upload_temp_user_file_to(
        user,
        filename,
        new_filename=new_filename,
        directory=directory
    ) == expected


@pytest.mark.parametrize('filename,new_filename,directory,expected', [
    ('test.pdf', 'SavedFile', 'd', 'users/1/d/savedfile.pdf'),
    ('test.pdf', 'saved file.pdf', 'd', 'users/1/d/savedfile.pdf'),
    ('test.pdf', 'SavedFile', None, 'users/1/savedfile.pdf'),
    ('test.pdf', None, None, 'users/1/test.pdf')
])
def test_upload_user_file_to(user, filename, new_filename, directory, expected):
    assert upload_user_file_to(
        user,
        filename,
        new_filename=new_filename,
        directory=directory
    ) == expected
