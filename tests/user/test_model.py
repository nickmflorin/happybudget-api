import pytest


@pytest.mark.parametrize('filename,directory,expected', [
    ('SavedFile.jpg', 'd', 'users/1/temp/d/savedfile.jpg'),
    ('Saved File.jpg', 'd', 'users/1/temp/d/savedfile.jpg'),
    ('test.jpg', None, 'users/1/temp/test.jpg')
])
def test_upload_temp_user_image_to(user, filename, directory, expected):
    assert user.upload_temp_image_to(filename, directory=directory) == expected


@pytest.mark.parametrize('filename,directory,expected', [
    ('SavedFile.jpg', 'd', 'users/1/d/savedfile.jpg'),
    ('saved file.jpg', 'd', 'users/1/d/savedfile.jpg'),
    ('savedfile.jpg', None, 'users/1/savedfile.jpg')
])
def test_upload_user_image_to(user, filename, directory, expected):
    assert user.upload_image_to(filename, directory=directory) == expected


@pytest.mark.parametrize('filename,directory,expected', [
    ('SavedFile.pdf', 'd', 'users/1/temp/d/savedfile.pdf'),
    ('Saved File.pdf', 'd', 'users/1/temp/d/savedfile.pdf'),
    ('test.pdf', None, 'users/1/temp/test.pdf')
])
def test_upload_temp_user_file_to(user, filename, directory, expected):
    assert user.upload_temp_file_to(filename, directory=directory) == expected


@pytest.mark.parametrize('filename,directory,expected', [
    ('SavedFile.pdf', 'd', 'users/1/d/savedfile.pdf'),
    ('saved file.pdf', 'd', 'users/1/d/savedfile.pdf'),
    ('savedfile.pdf', None, 'users/1/savedfile.pdf')
])
def test_upload_user_file_to(user, filename, directory, expected):
    assert user.upload_file_to(filename, directory=directory) == expected
