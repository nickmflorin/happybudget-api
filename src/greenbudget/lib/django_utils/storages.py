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


class FileNameError(Exception):
    def __init__(self, filename):
        self._filename = filename

    def __str__(self):
        return "Filename %s is invalid." % self._filename


class FileExtensionError(Exception):
    pass


class MissingFileExtension(FileNameError, FileExtensionError):
    def __init__(self, filename):
        FileNameError.__init__(self, filename)

    def __str__(self):
        return "No extension found on filename %s." % self._filename


class UnsupportedImageExtension(FileExtensionError):
    def __init__(self, ext):
        self._ext = ext

    def __str__(self):
        return "Unsupported image extension %s." % self._ext


def using_s3_storage():
    storage_cls = get_storage_class()
    return storage_cls is S3Boto3Storage


def validate_filename(filename):
    boolean_mask = [x for x in [s == '.' for s in filename] if x is True]
    if len(boolean_mask) == 0:
        raise MissingFileExtension(filename)
    elif len(boolean_mask) != 1:
        raise FileNameError(filename)


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
            raise MissingFileExtension(filename)
        return None
    return ext


def get_image_filename_extension(filename, strict=True):
    try:
        ext = get_filename_extension(filename, strict=strict)
    except MissingFileExtension as e:
        raise MissingFileExtension(e.args)
    except FileNameError as e:
        raise FileNameError(e.args)
    else:
        if ext not in settings.ACCEPTED_IMAGE_EXTENSIONS:
            if strict:
                raise UnsupportedImageExtension(ext)
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
