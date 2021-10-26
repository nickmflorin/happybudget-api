from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions


class IOErrorCodes:
    INVALID_FILE_NAME = "invalid_file_name"
    INVALID_FILE_EXTENSION = "invalid_file_extension"


class FileNameError(exceptions.ValidationError):
    default_detail = _("The file name is invalid.")
    default_code = IOErrorCodes.INVALID_FILE_NAME
    default_info_detail = "The file name `{filename}` is invalid."

    def __init__(self, *args, **kwargs):
        filename = kwargs.pop('filename', None)
        super().__init__(*args, **kwargs)
        if filename is not None:
            self.detail = exceptions.ErrorDetail(
                _(self.default_info_detail.format(filename=filename)),
                code=kwargs.get('code', self.default_code)
            )


class FileExtensionError(exceptions.ValidationError):
    default_detail = _("The file extension is invalid.")
    default_code = IOErrorCodes.INVALID_FILE_EXTENSION
    default_info_detail = "The file extension `{ext}` is invalid."

    def __init__(self, *args, **kwargs):
        ext = kwargs.pop('ext', None)
        super().__init__(*args, **kwargs)
        if ext is not None:
            self.detail = exceptions.ErrorDetail(
                _(self.default_info_detail.format(ext=ext)),
                code=kwargs.get('code', self.default_code)
            )


class MissingFileExtension(FileNameError):
    default_detail = _("The file name extension is missing an extension.")
    default_info_detail = "The file name `{filename}` is missing an extension."


class UnsupportedFileExtension(FileExtensionError):
    default_detail = _("The file extension is not supported.")
    default_info_detail = "The file extension `{ext}` is not supported."
