import base64
import binascii
import imghdr
import logging

from botocore import exceptions
from django.conf import settings

from .exceptions import (
    MissingFileExtensionError,
    UnsupporedFileExtensionError,
    FileValidationError,
    FileDoesNotExistError,
    FileExtensionError
)
from .storages import using_s3_storage


logger = logging.getLogger('happybudget')


def is_base64_encoded_string(data):
    if 'data:' in data and ';base64,' in data:
        _, data = data.split(';base64,')
    try:
        return base64.b64encode(base64.b64decode(data)) == data
    except binascii.Error:
        return False


def parse_filename(filename, supported=None, error_field=None):
    if '.' not in filename:
        raise MissingFileExtensionError(
            field=error_field,
            filename=filename
        )
    ext = filename.split('.')[-1].strip().lower()
    if ext == "":
        raise MissingFileExtensionError(
            field=error_field,
            filename=filename
        )
    if supported is not None and ext not in supported:
        raise UnsupporedFileExtensionError(field=error_field, ext=ext)
    return f"{filename.split('.')[0].replace(' ', '').lower()}.{ext}", ext


def parse_image_filename(filename, error_field=None):
    return parse_filename(
        filename=filename,
        error_field=error_field,
        supported=settings.ACCEPTED_IMAGE_EXTENSIONS
    )


class handle_file_existence_errors:
    """
    Wraps a function such that errors related to the non-existence of a file
    object while executing that function are handled.

    The specific file system that is used for storage depends on the environment,
    but will either be: (1) AWS-backed storarage (S3) or
    (2) Local File System Storage:

    (1) AWS Storage (S3)
        When using S3 as a file storage system, in the case that the referenced
        file location saved to the DB no longer exists in AWS, the raised
        exception will be an instance of :obj:`botocore.exceptions.ClientError`.

        This often happens when temporarily using S3 storage in local
        development, as the previously saved references for the file locations
        are based on the local file system storage and cannot be found in S3.

    (2) Local File System Storage
        When using the Local File System as a file storage system, in the case
        that the referenced file location saved to the DB no longer exists in
        the local file system, Python's builtin :obj:`FileNotFoundError` will
        be raised.

    In both cases, this wrapper gives the calling logic a chance to fail more
    gracefully and conditionally handle cases of non-existent file locations
    on a case-by-case basis.
    """
    def __init__(self, func, url, **kwargs):
        self._func = func
        self._url = url
        assert isinstance(url, str) or hasattr(url, '__call__'), \
            "The provided URL must either be a string or a callable."
        self._strict = kwargs.pop('strict', True)

    def url(self, *args, **kwargs):
        if isinstance(self._url, str):
            return self._url
        return self._url(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        try:
            return self._func(*args, **kwargs)
        except exceptions.ClientError as e:
            # TODO: We should more carefully check if the ClientError refers to
            # the file not existing at that location anymore.  While it will
            # most likely refer to that case, there could potentially be other
            # errors that ClientError refers to.
            if self._strict:
                raise FileDoesNotExistError(
                    source="aws",
                    location=self.url(*args, **kwargs)
                ) from e
            logger.exception(
                f"Could not find image {self.url(*args, **kwargs)} in AWS.")
            return None
        except FileNotFoundError as e:
            if self._strict:
                raise FileDoesNotExistError(
                    source="local",
                    location=self.url(*args, **kwargs)
                ) from e
            logger.error(
                f"Could not find image {self.url(*args, **kwargs)} locally.")
            return None


def get_file_attribute(file_obj, attr, strict=True):
    return handle_file_existence_errors(
        func=getattr,
        strict=strict,
        url=lambda f: f.url
    )(file_obj, attr)


def get_local_extension(path, *args, strict=True):
    try:
        # Note that imghdr uses the local file system.
        return imghdr.what(path, *args)
    except FileNotFoundError as e:
        if strict:
            raise FileDoesNotExistError(
                source="local",
                location=path
            ) from e
        logger.error(
            f"Could not parse extension as file {path} could not "
            "be found locally."
        )
        return None


def get_aws_extension(path, strict=True):
    try:
        # Note: We do not need to be concerned with supported extensions
        # because we are just reading the extension of an existing file, not
        # validating whether or not a provided filename is valid.
        return parse_filename(path)[1]
    except FileValidationError as e:
        if strict:
            raise FileExtensionError(
                source="aws",
                location=path
            ) from e
        logger.error("Corrupted file name stored in AWS.", extra={
            "fname": path,
            "exception": e
        })
        return None


def get_extension(file_obj, strict=True, strict_extension=None):
    """
    Returns the extension that is associated with a given
    :obj:`django.db.models.fields.files.FieldFile`.

    The mannner in which the extension is determined is based on the specific
    file storage system being used, which depends on the environment.  It will
    either be: (1) AWS-backed storarage (S3) or (2) Local File System Storage:

    (1) AWS Storage (S3)
        When using S3 as a file storage system, the extension is determined
        by parsing the filename.

        Note that this means if the file's previously saved path no longer
        exists in AWS, an error will not be raised - since only the name is
        required to determine the extension.

    (2) Local File System Storage
        When using the Local File System as a file storage system, the extension
        is determined by physically looking at what type of file is stored
        at the path previously saved with that file object.

        Note that this means if the file's previously saved path no longer
        exists in the local file storage system, an error will be raised.
    """
    if using_s3_storage():
        return get_aws_extension(
            file_obj.path, strict=strict and strict_extension is not False)
    return get_local_extension(file_obj.path, strict=strict)
