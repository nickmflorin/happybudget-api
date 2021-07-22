from storages.backends.s3boto3 import S3Boto3Storage
import os

from django.conf import settings
from django.core.files.storage import FileSystemStorage


class BaseStorageMixin:
    def file_name(self, name):
        if self._subdirectory is not None:
            return os.path.join(self._subdirectory, name)
        return name


class S3StorageBase(S3Boto3Storage, BaseStorageMixin):
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME

    def __init__(self, *args, **kwargs):
        self._subdirectory = kwargs.pop('sub_directory', None)
        super().__init__(*args, **kwargs)

    def url(self, name):
        if self._subdirectory is not None:
            name = os.path.join(self._subdirectory, name)
        return super().url(name)


class LocalStorage(FileSystemStorage, BaseStorageMixin):
    def __init__(self, *args, **kwargs):
        self._subdirectory = kwargs.pop('sub_directory', None)
        if self._subdirectory is not None:
            kwargs['location'] = os.path.join(
                settings.MEDIA_ROOT, self._subdirectory)
        super().__init__(*args, **kwargs)

    def url(self, name):
        url = super().url(self.file_name(name))
        if url.startswith("/"):
            url = url[1:]
        return os.path.join(settings.APP_URL, url)


def S3ToggleStorageBase():
    if getattr(settings, 'AWS_STORAGE', False) is True:
        return S3StorageBase
    return LocalStorage


def S3ToggleStorage(*args, **kwargs):
    storage_cls = S3ToggleStorageBase()
    return storage_cls(*args, **kwargs)
