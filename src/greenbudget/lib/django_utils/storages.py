import os

from django.conf import settings
from django.core.files.storage import FileSystemStorage


class LocalStorage(FileSystemStorage):
    def url(self, name):
        url = super().url(name)
        if url.startswith("/"):
            url = url[1:]
        return os.path.join(settings.APP_URL, url)


class ImageExtensionError(Exception):
    pass


class MissingImageExtension(ImageExtensionError):
    def __init__(self, filename):
        self._filename = filename

    def __str__(self):
        return "No extension found on filename %s." % self._filename


class UnsupportedImageExtension(ImageExtensionError):
    def __init__(self, ext):
        self._ext = ext

    def __str__(self):
        return "Unsupported image extension %s." % self._ext


def using_s3_storage():
    return settings.DEFAULT_FILE_STORAGE == 'storages.backends.s3boto3.S3Boto3Storage'  # noqa


def get_image_filename_extension(filename, strict=True):
    if '.' not in filename:
        if strict:
            raise MissingImageExtension(filename)
        return None
    ext = filename.split('.')[-1]
    if ext.strip().lower() not in settings.ACCEPTED_IMAGE_EXTENSIONS:
        if strict:
            raise UnsupportedImageExtension(ext)
        return None
    return ext.strip().lower()


def get_image_filename(filename, new_filename=None):
    new_filename = new_filename or filename
    extension = get_image_filename_extension(filename, strict=True)

    new_extension = get_image_filename_extension(new_filename, strict=False)
    if new_extension is not None and new_extension != extension:
        raise Exception("Conflicting file extensions %s and %s." %
                        (extension, new_extension))

    return f"{new_filename.replace(' ', '').lower()}.{extension}"
