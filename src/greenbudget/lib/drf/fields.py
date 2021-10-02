import base64
import binascii
import imghdr
import uuid

from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from greenbudget.lib.django_utils.storages import (
    using_s3_storage, get_image_filename_extension)


def find_field_original_serializer(field):
    parent = field.parent
    while parent is not None:
        new_parent = parent.parent
        if new_parent is None:
            break
        parent = new_parent
    return parent


class GenericRelatedField(serializers.PrimaryKeyRelatedField):
    default_error_messages = {
        'incorrect_type': _(
            'Incorrect type. Expected dict value with `id` and `type`, '
            'received {data_type}.'
        ),
        'incorrect_generic_type': _(
            'Incorrect model type. Expected {model_types} received '
            '{model_type}.'
        ),
    }

    def __init__(self, *args, **kwargs):
        self._model_classes = kwargs.pop('model_classes', {})
        if len(self._model_classes) == 0 or len(self._model_classes) == 1:
            raise Exception("Must provide at least two model classes to map.")
        super().__init__(*args, **kwargs)

    def get_model_cls(self, data):
        return self._model_classes[data["type"]]

    def get_queryset(self, data):
        model_cls = self.get_model_cls(data)
        return model_cls.objects.all()

    def to_internal_value(self, data):
        try:
            queryset = self.get_queryset(data)
        except KeyError:
            self.fail(
                'incorrect_generic_type',
                model_type=data['type'],
                model_types=", ".join(self._model_classes.keys())
            )
        else:
            try:
                pk = data['id']
                if isinstance(pk, bool):
                    raise TypeError
                return queryset.get(pk=pk)
            except ObjectDoesNotExist:
                self.fail('does_not_exist', pk_value=pk)
            except (TypeError, ValueError, KeyError):
                self.fail('incorrect_type', data_type=type(data).__name__)


class ModelChoiceField(serializers.ChoiceField):
    """
    A :obj:`rest_framework.serializers.ModelSerializer` field that allows
    :obj:`django.db.models.Model` fields that have distinct choices to be
    represented by both their internal database reference and their display
    name.

    Write operations will still be referenced by just the internal database
    reference where as read operations will serialize both the internal ref
    and the display name/label.

    class MyModel(models.Model):
        FRUITS = Choices(
            (0, "apple", "Apple"),
            (1, "banana", "Banana"),
            (2, "strawberry", "Strawberry"),
        )
        fruit = models.IntegerField(choices=FRUITS)

    class MyModelSerializer(serializers.ModelSerializer):
        fruit = ModelChoiceField(source='FRUITS')

    PATCH "/models/<pk>/" {"fruit": 0}
    >>> {"fruit": {"name": "Apple", "id": 0}}

    GET "/models/pk/"
    >>> {"fruit": {"name": "Apple", "id": 0}}
    """

    def to_representation(self, value):
        if value is not None:
            return {'id': value, 'name': self.choices[value]}
        return value


class ImageFieldFileSerializer(serializers.Serializer):
    url = serializers.URLField(read_only=True)
    size = serializers.IntegerField(read_only=True)
    width = serializers.IntegerField(read_only=True)
    height = serializers.IntegerField(read_only=True)
    extension = serializers.SerializerMethodField()

    def get_extension(self, instance):
        # Note that imghdr uses the local file system, so it will look at the
        # file in the local file system.  This only works when we are in local
        # development, because we are using
        # django.core.files.storage.FileSystemStorage.  When we are are in
        # a production/dev environment, and we are using
        # storages.backends.s3boto3.S3Boto3Storage, we need to use an alternate
        # method to find the extension.
        if using_s3_storage():
            extension = get_image_filename_extension(instance.name)
        else:
            extension = imghdr.what(instance.path)
        return "jpg" if extension == "jpeg" else extension


def is_base64_encoded_string(data):
    if 'data:' in data and ';base64,' in data:
        _, data = data.split(';base64,')
    try:
        return base64.b64encode(base64.b64decode(data)) == data
    except binascii.Error:
        return False


class Base64ImageField(serializers.ImageField):
    """
    A :obj:`rest_framework.serializers.ImageField` field that allows image
    uploads via raw POST data.  It uses base64 for encoding/decoding the
    contents of the file.
    """

    def to_representation(self, instance):
        if instance is not None:
            try:
                return ImageFieldFileSerializer(instance).data
            except ValueError:
                # This will happen if hte instance does not have a file
                # associated with it.
                return super().to_representation(instance)
        return super().to_representation(instance)

    def to_internal_value(self, data):
        if data is not None:
            if isinstance(data, str):
                if 'data:' in data and ';base64,' in data:
                    header, data = data.split(';base64,')
                try:
                    decoded_file = base64.b64decode(data)
                except TypeError:
                    self.fail('invalid_image')
                file_name = str(uuid.uuid4())[:12]
                file_extension = self.get_file_extension(file_name, decoded_file)
                complete_file_name = "%s.%s" % (file_name, file_extension, )
                data = ContentFile(decoded_file, name=complete_file_name)

        return super(Base64ImageField, self).to_internal_value(data)

    def get_file_extension(self, file_name, decoded_file):
        extension = imghdr.what(file_name, decoded_file)
        return "jpg" if extension == "jpeg" else extension
