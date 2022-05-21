import base64
import logging
import uuid

from django.core.files.base import ContentFile
from django.forms.fields import ImageField as _ImageField

from rest_framework import serializers

from .exceptions import FileError
from .utils import (
    get_extension, get_local_extension, handle_file_existence_errors)


logger = logging.getLogger('happybudget')


class NoValidationDjangoImageField(_ImageField):
    default_validators = []


class ImageField(serializers.ImageField):
    """
    By default, DRF's :obj:`serializers.ImageField` will perform it's own
    validation using Django's :obj:`forms.ImageField`.  The only validation it
    performs is validating that the image extension is valid - which we want to
    do ourselves, both because we want to restrict to a more selective set of
    image extensions and we want to raise the validation errors in our own
    context, so they conform to our set or error codes.

    In order to do this, we need to mutate :obj:`serializers.ImageField` to
    use an extension of Django's :obj:`forms.ImageField` that does not perform
    the extension validation.
    """

    def __init__(self, *args, **kwargs):
        kwargs['_DjangoImageField'] = NoValidationDjangoImageField
        super().__init__(*args, **kwargs)


class FileIntegerField(serializers.IntegerField):
    """
    An extension of :obj:`rest_framework.serializers.IntegerField` that wraps
    the attribute lookup on the :obj:`django.db.models.fields.files.FieldFile`
    such that errors related to the file not existing at the expected path
    are either gracefully handled or converted to internal standardized
    exceptions that the serializer this field belongs to can handle.
    """
    def __init__(self, *args, **kwargs):
        self._strict = kwargs.pop('strict', True)
        kwargs['read_only'] = True
        super().__init__(*args, **kwargs)

    def get_attribute(self, instance):
        parent_method = handle_file_existence_errors(
            super().get_attribute,
            url=lambda obj: obj.file.url,
            strict=self._strict
        )
        return parent_method(instance)


class FileExtensionField(serializers.CharField):
    """
    An extension of :obj:`rest_framework.serializers.CharField` that finds
    the extension a given :obj:`django.db.models.fields.files.FieldFile` is
    associated with, while properly handling cases that the file may no longer
    exist or the extension cannot be determined.
    """
    def __init__(self, *args, **kwargs):
        self._strict = kwargs.pop('strict', True)
        self._strict_extension = kwargs.pop('strict_extension', True)
        kwargs['read_only'] = True
        super().__init__(*args, **kwargs)

    def to_representation(self, instance):
        return get_extension(
            instance,
            strict=self._strict,
            strict_extension=self._strict_extension
        )


class Base64ImageField(serializers.ImageField):
    """
    A :obj:`rest_framework.serializers.ImageField` field that allows image
    uploads via raw POST data.  It uses base64 for encoding/decoding the
    contents of the file.
    """

    def to_representation(self, instance):
        """
        Returns a serialized representation of the
        :obj:`django.core.files.images.ImageFile` instance using the
        :obj:`ImageFileFieldSerializer`.

        Note:
        ----
        In the case that the image associated with the
        :obj:`django.core.files.images.ImageFile` cannot be found, there are
        two things to consider:

        (1) The URL will still be accessible on the instance without raising an
            exception, but accessing the `size`, `width`, `height` or other
            attributes will raise an exception indicating the file cannot be
            found.

        (2) The parent `.to_representation()` method of the base
            :obj:rest_framework.serializers.ImageField` class will simply return
            the string URL, regardless of whether or not the file associated
            with that URL actually exists.

        Since this serializer returns a serialized object representation of the
        :obj:`django.core.files.images.ImageFile` instance, that includes the
        `size, `width` and `height` attributes - attempting to serialize the
        instance if the URL is invalid or cannot be found will result in an
        exception indicating that the file cannot be found.

        In this case, we *do not* want to use the parent `.to_representation()`
        method, because it will return the invalid URL - which will cause errors
        in the FE - so we simply return None and log warnings.
        """
        # pylint: disable=import-outside-toplevel
        from .serializers import ImageFileFieldSerializer

        # Note: The value of an image field will never be None, but it defines
        # a __bool__ method that returns whether or not there is a file
        # associated with it.
        if instance:
            try:
                return ImageFileFieldSerializer(instance).data
            except FileError:
                # Avoid using the parent `.to_representation()` method, see note
                # in docstring.
                return None
        # It is okay to call the parent `.to_representation()` method because
        # it will return None in the case that the instance does not exist.
        return super().to_representation(instance)

    def to_internal_value(self, data):
        if data is not None:
            if isinstance(data, str):
                if 'data:' in data and ';base64,' in data:
                    _, data = data.split(';base64,')
                try:
                    decoded_file = base64.b64decode(data)
                except TypeError:
                    self.fail('invalid_image')
                file_name = str(uuid.uuid4())[:12]
                file_extension = get_local_extension(file_name, decoded_file)
                file_extension = "jpg" if file_extension == "jpeg" \
                    else file_extension
                complete_file_name = "%s.%s" % (file_name, file_extension, )
                data = ContentFile(decoded_file, name=complete_file_name)

        return super().to_internal_value(data)
