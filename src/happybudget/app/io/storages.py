import os
from storages.backends.s3boto3 import S3Boto3Storage

from django.conf import settings
from django.core.files.storage import FileSystemStorage, get_storage_class


class LocalStorage(FileSystemStorage):
    def url(self, name):
        url = super().url(name)
        if url.startswith("/"):
            url = url[1:]
        return os.path.join(str(settings.APP_URL), url)


def using_s3_storage():
    storage_cls = get_storage_class()
    return storage_cls is S3Boto3Storage
