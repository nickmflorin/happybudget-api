import base64
import binascii

from django.conf import settings

from .exceptions import (
    MissingFileExtension, FileNameError, UnsupportedFileExtension,
    FileExtensionError)


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


def upload_temp_user_image_to(user, filename, directory=None, new_filename=None):  # noqa
    filename = get_image_filename(filename, new_filename=new_filename)
    if directory is not None:
        return f'{user_temp_storage_directory(user)}/{directory}/{filename}'
    return f'{user_temp_storage_directory(user)}/{filename}'


def upload_user_image_to(user, filename, directory=None, new_filename=None):
    filename = get_image_filename(filename, new_filename=new_filename)
    if directory is not None:
        return f'{user_storage_directory(user)}/{directory}/{filename}'
    return f'{user_storage_directory(user)}/{filename}'


def upload_temp_user_file_to(user, filename, directory=None, new_filename=None):
    filename = get_filename(filename, new_filename=new_filename)
    if directory is not None:
        return f'{user_temp_storage_directory(user)}/{directory}/{filename}'
    return f'{user_temp_storage_directory(user)}/{filename}'


def upload_user_file_to(user, filename, directory=None, new_filename=None):
    filename = get_filename(filename, new_filename=new_filename)
    if directory is not None:
        return f'{user_storage_directory(user)}/{directory}/{filename}'
    return f'{user_storage_directory(user)}/{filename}'


def validate_filename(filename):
    boolean_mask = [x for x in [s == '.' for s in filename] if x is True]
    if len(boolean_mask) == 0:
        raise MissingFileExtension(filename=filename)
    elif len(boolean_mask) != 1:
        raise FileNameError(filename=filename)


def get_filename_extension(filename, strict=True):
    try:
        validate_filename(filename)
    except FileNameError as e:
        if strict:
            raise e
        return None
    ext = filename.split('.')[-1].strip().lower()
    if ext == "":
        if strict:
            raise MissingFileExtension(filename=filename)
        return None
    return ext


def get_image_filename_extension(filename, strict=True):
    ext = get_filename_extension(filename, strict=strict)
    if ext is not None and ext not in settings.ACCEPTED_IMAGE_EXTENSIONS:
        if strict:
            raise UnsupportedFileExtension(ext=ext)
        return None
    return ext


def get_filename(filename, new_filename=None, getter=None):
    new_filename = new_filename or filename
    getter = getter or get_filename_extension

    extension = getter(filename, strict=True)
    new_extension = getter(new_filename, strict=False)

    if new_extension is not None:
        if new_extension != extension:
            raise FileExtensionError(
                "Conflicting file extensions %s and %s." %
                (extension, new_extension)
            )
        new_filename = new_filename.split('.')[0]

    return f"{new_filename.replace(' ', '').lower()}.{extension}"


def get_image_filename(filename, new_filename=None):
    return get_filename(
        filename=filename,
        new_filename=new_filename,
        getter=get_image_filename_extension,
    )
