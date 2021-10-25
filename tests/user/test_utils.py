import pytest

from greenbudget.app.user.utils import (
    upload_user_image_to,
    upload_temp_user_image_to,
    upload_user_file_to,
    upload_temp_user_file_to
)


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
