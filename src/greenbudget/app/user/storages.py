from greenbudget.lib.django_utils.storages import S3ToggleStorageBase

from .utils import user_image_temp_directory


class TempUserImageStorage(S3ToggleStorageBase()):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        kwargs['sub_directory'] = user_image_temp_directory(user)
        super().__init__(*args, **kwargs)


#     base_storage_cls = S3ToggleStorageBase()
#     if getattr(settings, 'AWS_STORAGE', False) is True:
#         return base_storage_cls

#     class TempLocalUserImageStorage(base_storage_cls):
#         def __init__(self, *args, **kwargs):
#             user = kwargs.pop('user')
#             kwargs['sub_directory'] = user_image_temp_directory(user)
#             super().__init__(*args, **kwargs)

#     class TempS3UserImageStorage(base_storage_cls):
#         def __init__(self, *args, **kwargs):

#     return TempLocalUserImageStorage


# TempUserImageStorage = _TempUserImageStorage()
