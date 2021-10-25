from greenbudget.lib.django_utils.storages import (
    get_image_filename, get_filename)


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
