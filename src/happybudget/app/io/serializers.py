import logging
import os

from django.core.files.storage import get_storage_class
from django.db import models

from rest_framework import serializers

from happybudget.app import exceptions
from happybudget.app.serializers import ModelSerializer, Serializer

from .exceptions import FileError
from .fields import ImageField, FileExtensionField, FileIntegerField
from .models import Attachment
from .utils import parse_filename, get_extension


logger = logging.getLogger('happybudget')


class ImageFileFieldSerializer(Serializer):
    url = serializers.URLField(read_only=True)
    size = FileIntegerField(strict=True)
    width = FileIntegerField(strict=True)
    height = FileIntegerField(strict=True)
    extension = serializers.SerializerMethodField()

    def get_extension(self, instance):
        # If the filename in AWS is malformed, just return None for the
        # extension.
        return get_extension(instance, strict_extension=False)


class AttachmentListSerializer(serializers.ListSerializer):
    """
    An implementation of :obj:`rest_framework.serializers.ListSerializer` that
    is used when serializing instances of :obj:`Attachment`.

    This implementation will remove serialized instances of a :obj:`Attachment`
    in the case that the file associated with the :obj:`Attachment` no longer
    exists in the local file storage system or in AWS.  This avoids potential
    hard 500 errors when there is a single corrupted :obj:`Attachment` in a
    set.

    Note:
    ----
    We do not need to worry about these 500 errors in the case that the list
    serializer class is not being used, because there are currently no detail
    endpoints (i.e. GET /attachments/<pk>/) associated with the :obj:`Attachment`
    model.
    """
    def to_representation(self, data):
        iterable = data.all() if isinstance(data, models.Manager) else data
        children_representations = []
        for i in iterable:
            try:
                children_representations.append(self.child.to_representation(i))
            except FileError as e:
                logger.error(e)
        return children_representations


class SimpleAttachmentSerializer(ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(read_only=True)
    name = serializers.SerializerMethodField()
    url = serializers.URLField(read_only=True, source='file.url')
    # If the filename in AWS is malformed, just return None for the extension.
    extension = FileExtensionField(source='file', strict_extension=False)

    class Meta:
        model = Attachment
        list_serializer_class = AttachmentListSerializer
        fields = ('id', 'name', 'url', 'extension')

    def get_name(self, instance):
        return os.path.basename(instance.file.name)


class AttachmentSerializer(SimpleAttachmentSerializer):
    size = FileIntegerField(read_only=True, source='file.size', strict=True)

    class Meta(SimpleAttachmentSerializer.Meta):
        model = Attachment
        list_serializer_class = AttachmentListSerializer
        fields = SimpleAttachmentSerializer.Meta.fields + ('size', )


class UploadAttachmentSerializer(ModelSerializer):
    file = serializers.FileField(required=False)

    class Meta:
        model = Attachment
        fields = ('file', )

    def validate(self, attrs):
        parse_filename(attrs['file'].name, error_field='file')
        return attrs


class UploadAttachmentsSerializer(Serializer):
    file = serializers.FileField(required=False)
    files = serializers.ListField(
        child=serializers.FileField(),
        required=False
    )

    def validate(self, attrs):
        if 'file' not in attrs and 'files' not in attrs:
            raise exceptions.ValidationError(
                "Either `file` or `files` parameters must be specified.")
        files = attrs.pop('files', None)
        if files is None:
            files = [attrs.pop('file')]
        child_serializers = [UploadAttachmentSerializer(
            data={**{'file': f}, **attrs}
        ) for f in files]
        for serializer in child_serializers:
            serializer.is_valid(raise_exception=True)
        return {'serializers': child_serializers}

    def create(self, validated_data):
        child_serializers = validated_data.pop('serializers')
        attachments = [
            serializer.save(**validated_data)
            for serializer in child_serializers
        ]
        return attachments


class AbstractTempSerializer(Serializer):
    def create(self, validated_data):
        storage_cls = get_storage_class()
        storage = storage_cls()
        storage.save(validated_data["filename"], validated_data["file"].file)
        return storage.url(validated_data["filename"])


class TempFileSerializer(AbstractTempSerializer):
    file = serializers.FileField()

    def validate(self, attrs):
        filename = self.user.upload_temp_file_to(
            filename=attrs['file'].name,
            error_field='file'
        )
        return {'file': attrs['file'], "filename": filename}


class TempImageSerializer(AbstractTempSerializer):
    image = ImageField()

    def validate(self, attrs):
        image_name = self.user.upload_temp_image_to(
            filename=attrs['image'].name,
            error_field='image'
        )
        return {'file': attrs['image'], "filename": image_name}
