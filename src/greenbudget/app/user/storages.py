from greenbudget.lib.django_utils.storages import S3ToggleStorageBase

from .utils import user_image_temp_directory


class TempUserImageStorage(S3ToggleStorageBase()):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        kwargs['sub_directory'] = user_image_temp_directory(user)
        super().__init__(*args, **kwargs)
