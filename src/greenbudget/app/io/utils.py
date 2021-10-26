import base64
import binascii

from django.conf import settings

from .exceptions import (
    MissingFileExtension, FileNameError, UnsupportedFileExtension)


def is_base64_encoded_string(data):
    if 'data:' in data and ';base64,' in data:
        _, data = data.split(';base64,')
    try:
        return base64.b64encode(base64.b64decode(data)) == data
    except binascii.Error:
        return False


def user_storage_directory(user):
    return f'users/{user.pk}'


def user_temp_storage_directory(user):
    return f'{user_storage_directory(user)}/temp'


def upload_temp_user_image_to(user, filename, directory=None):
    filename, ext = parse_image_filename(filename)
    if directory is not None:
        return f'{user_temp_storage_directory(user)}/{directory}/{filename}'
    return f'{user_temp_storage_directory(user)}/{filename}'


def upload_user_image_to(user, filename, directory=None):
    filename, ext = parse_image_filename(filename)
    if directory is not None:
        return f'{user_storage_directory(user)}/{directory}/{filename}'
    return f'{user_storage_directory(user)}/{filename}'


def upload_temp_user_file_to(user, filename, directory=None):
    filename, ext = parse_filename(filename)
    if directory is not None:
        return f'{user_temp_storage_directory(user)}/{directory}/{filename}'
    return f'{user_temp_storage_directory(user)}/{filename}'


def upload_user_file_to(user, filename, directory=None):
    filename, ext = parse_filename(filename)
    if directory is not None:
        return f'{user_storage_directory(user)}/{directory}/{filename}'
    return f'{user_storage_directory(user)}/{filename}'


def parse_filename(filename, supported=None):
    boolean_mask = [x for x in [s == '.' for s in filename] if x is True]
    if len(boolean_mask) == 0:
        raise MissingFileExtension(filename=filename)
    elif len(boolean_mask) != 1:
        raise FileNameError(filename=filename)
    ext = filename.split('.')[-1].strip().lower()
    if ext == "":
        raise MissingFileExtension(filename=filename)
    if supported and ext not in supported:
        raise UnsupportedFileExtension(ext=ext)
    return f"{filename.split('.')[0].replace(' ', '').lower()}.{ext}", ext


def parse_image_filename(filename, strict=True):
    return parse_filename(filename, supported=settings.ACCEPTED_IMAGE_EXTENSIONS)
