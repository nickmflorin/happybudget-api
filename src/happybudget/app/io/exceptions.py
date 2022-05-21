from django.db.models.fields.files import FieldFile
from django.utils.translation import gettext_lazy as _

from happybudget.app import exceptions


class FileError(Exception):
    """
    Raised when there is an error related to a :obj:`django.db.models.FileField`
    that is either stored in the local file storage system or in AWS.
    """
    def __init__(self, source, location):
        assert source in ("aws", "local"), f"Invalid source {source} provided."
        self._source = source
        self._location = location
        if isinstance(location, FieldFile):
            self._location = location.url


class FileDoesNotExistError(FileError):
    """
    Raised when either the built in :obj:`FileNotFoundError` is raised in
    regard to a :obj:`django.db.models.FileField` that is stored locally, or
    a :obj:`botocore.exceptions.ClientError` is raised in regard to a
    :obj:`django.db.models.FileField` that is stored in AWS.
    """
    def __str__(self):
        if self._source == "aws":
            return f"Could not find file {self._location} in AWS."
        return f"Could not find file {self._location} locally."


class FileExtensionError(FileError):
    """
    Raised when the extension cannot be parsed from the filename associated with
    a :obj:`django.db.models.FileField` that is stored in AWS or in the local
    file storage system.
    """
    def __str__(self):
        if self._source == "aws":
            return (
                f"Extension could not be parsed for file {self._location} "
                "in AWS."
            )
        return (
            f"Extension could not be parsed for file {self._location} in the "
            "local file storage system."
        )


class IOErrorCodes:
    INVALID_FILE_NAME = "invalid_file_name"
    INVALID_FILE_EXTENSION = "invalid_file_extension"


class FileValidationError(exceptions.ValidationError):
    pass


class FileNameInvalidError(FileValidationError):
    default_detail = _("The file name is invalid.")
    default_code = IOErrorCodes.INVALID_FILE_NAME
    default_info_detail = "The file name `{filename}` is invalid."


class FileExtensionInvalidError(FileValidationError):
    default_detail = _("The file extension is invalid.")
    default_code = IOErrorCodes.INVALID_FILE_EXTENSION
    default_info_detail = "The file extension `{ext}` is invalid."


class MissingFileExtensionError(FileNameInvalidError):
    default_detail = _("The file name is missing an extension.")
    default_info_detail = "The file name `{filename}` is missing an extension."


class UnsupporedFileExtensionError(FileExtensionInvalidError):
    default_detail = _("The file extension is not supported.")
    default_info_detail = "The file extension `{ext}` is not supported."
