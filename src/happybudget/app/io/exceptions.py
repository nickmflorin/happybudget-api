from django.utils.translation import gettext_lazy as _
from happybudget.app import exceptions


class IOErrorCodes:
    INVALID_FILE_NAME = "invalid_file_name"
    INVALID_FILE_EXTENSION = "invalid_file_extension"


class FileError(exceptions.ValidationError):
    pass


class FileNameError(FileError):
    default_detail = _("The file name is invalid.")
    default_code = IOErrorCodes.INVALID_FILE_NAME
    default_info_detail = "The file name `{filename}` is invalid."


class FileExtensionError(FileError):
    default_detail = _("The file extension is invalid.")
    default_code = IOErrorCodes.INVALID_FILE_EXTENSION
    default_info_detail = "The file extension `{ext}` is invalid."


class MissingFileExtension(FileNameError):
    default_detail = _("The file name is missing an extension.")
    default_info_detail = "The file name `{filename}` is missing an extension."


class UnsupportedFileExtension(FileExtensionError):
    default_detail = _("The file extension is not supported.")
    default_info_detail = "The file extension `{ext}` is not supported."
