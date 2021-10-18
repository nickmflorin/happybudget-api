from greenbudget.lib.django_utils.storages import get_image_filename


def user_image_directory(user):
    return f'users/{user.pk}'


def user_image_temp_directory(user):
    return f'{user_image_directory(user)}/temp'


def upload_temp_user_image_to(user, filename, directory=None, new_filename=None):  # noqa
    filename = get_image_filename(filename, new_filename=new_filename)
    if directory is not None:
        return f'{user_image_temp_directory(user)}/{directory}/{filename}'
    return f'{user_image_temp_directory(user)}/{filename}'


def upload_user_image_to(user, filename, directory=None, new_filename=None):
    filename = get_image_filename(filename, new_filename=new_filename)
    if directory is not None:
        return f'{user_image_directory(user)}/{directory}/{filename}'
    return f'{user_image_directory(user)}/{filename}'
