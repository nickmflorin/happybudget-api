import base64
import binascii

from django.conf import settings

from .exceptions import MissingFileExtension, UnsupportedFileExtension


def is_base64_encoded_string(data):
    if 'data:' in data and ';base64,' in data:
        _, data = data.split(';base64,')
    try:
        return base64.b64encode(base64.b64decode(data)) == data
    except binascii.Error:
        return False


def parse_filename(filename, supported=None, error_field=None):
    if '.' not in filename:
        raise MissingFileExtension(field=error_field, filename=filename)
    ext = filename.split('.')[-1].strip().lower()
    if ext == "":
        raise MissingFileExtension(field=error_field, filename=filename)
    if supported is not None and ext not in supported:
        raise UnsupportedFileExtension(field=error_field, ext=ext)
    return f"{filename.split('.')[0].replace(' ', '').lower()}.{ext}", ext


def parse_image_filename(filename, error_field=None):
    return parse_filename(
        filename=filename,
        error_field=error_field,
        supported=settings.ACCEPTED_IMAGE_EXTENSIONS
    )
