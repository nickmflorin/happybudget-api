import imghdr
import logging
import os

from django.core.files.storage import get_storage_class

from rest_framework import serializers

from happybudget.app import exceptions
from happybudget.app.serializers import ModelSerializer, Serializer

from .exceptions import FileError
from .fields import ImageField
from .models import Attachment
from .storages import using_s3_storage
from .utils import parse_filename, parse_image_filename


logger = logging.getLogger('happybudget')


class ImageFileFieldSerializer(Serializer):
    url = serializers.URLField(read_only=True)
    size = serializers.IntegerField(read_only=True)
    width = serializers.IntegerField(read_only=True)
    height = serializers.IntegerField(read_only=True)
    extension = serializers.SerializerMethodField()

    def get_extension(self, instance, parser=None):
        parser = parser or parse_image_filename
        if using_s3_storage():
            try:
                return parser(instance.name)[1]
            except FileError as e:
                # This should not happen as the usage of this serializer should
                # be avoided in cases where the image cannot be found.
                logger.error("Corrupted file name stored in AWS.", extra={
                    "fname": instance.name,
                    "exception": e
                })
                return None
        try:
            # Note that imghdr uses the local file system, so it will look at
            # the file in the local file system.  This only works when we are
            # in local development, because we are using Django's
            # FileSystemStorage.
            return imghdr.what(instance.path)
        except FileNotFoundError:
            # This should not happen as the usage of this serializer should
            # be avoided in cases where the image cannot be found.
            logger.error(f"Could not find image {instance.url} locally.")


class SimpleAttachmentSerializer(ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(read_only=True)
    name = serializers.SerializerMethodField()
    url = serializers.URLField(read_only=True, source='file.url')
    extension = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = ('id', 'name', 'extension', 'url')

    def get_name(self, instance):
        return os.path.basename(instance.file.name)

    def get_extension(self, instance):
        return ImageFileFieldSerializer.get_extension(
            self, instance.file, parser=parse_filename)


class AttachmentSerializer(SimpleAttachmentSerializer):
    size = serializers.IntegerField(read_only=True, source='file.size')

    class Meta(SimpleAttachmentSerializer.Meta):
        model = Attachment
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
