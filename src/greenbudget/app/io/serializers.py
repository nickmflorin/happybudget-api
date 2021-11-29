import imghdr
import logging
import os

from django.core.files.storage import get_storage_class

from rest_framework import serializers, exceptions

from .exceptions import FileError
from .fields import ImageField
from .models import Attachment
from .storages import using_s3_storage
from .utils import (
    parse_filename,
    parse_image_filename,
    upload_temp_user_image_to,
    upload_temp_user_file_to
)


logger = logging.getLogger('greenbudget')


class ExtensionSerializerMixin:
    def get_extension(self, name, path=None):
        # Note that imghdr uses the local file system, so it will look at the
        # file in the local file system.  This only works when we are in local
        # development, because we are using Django's FileSystemStorage.
        if using_s3_storage():
            try:
                return parse_image_filename(name)[1]
            except FileError as e:
                logger.error("Corrupted image path stored in AWS.", extra={
                    "filename": name,
                    "exception": e
                })
                return None
        try:
            path = path or name
            return imghdr.what(path)
        except FileNotFoundError as e:
            logger.error("Corrupted image path stored locally.", extra={
                "filepath": path,
                "exception": e
            })
            return None


class ImageFileSerializer(ExtensionSerializerMixin, serializers.Serializer):
    url = serializers.URLField(read_only=True)
    size = serializers.IntegerField(read_only=True)
    width = serializers.IntegerField(read_only=True)
    height = serializers.IntegerField(read_only=True)
    extension = serializers.SerializerMethodField()

    def get_extension(self, instance):
        return super().get_extension(instance.name)


class SimpleAttachmentSerializer(
        ExtensionSerializerMixin, serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(read_only=True)
    name = serializers.SerializerMethodField()
    extension = serializers.SerializerMethodField()
    url = serializers.URLField(read_only=True, source='file.url')

    class Meta:
        model = Attachment
        fields = ('id', 'name', 'extension', 'url')

    def get_extension(self, instance):
        if using_s3_storage():
            return super().get_extension(instance.file.name)
        return super().get_extension(instance.file.name, instance.file.path)

    def get_name(self, instance):
        return os.path.basename(instance.file.name)


class AttachmentSerializer(SimpleAttachmentSerializer):
    size = serializers.IntegerField(read_only=True, source='file.size')

    class Meta(SimpleAttachmentSerializer.Meta):
        model = Attachment
        fields = SimpleAttachmentSerializer.Meta.fields + ('size', )


class UploadAttachmentSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=False)

    class Meta:
        model = Attachment
        fields = ('file', )

    def validate(self, attrs):
        parse_filename(attrs['file'].name, error_field='file')
        return attrs


class UploadAttachmentsSerializer(serializers.Serializer):
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
        serializers = [UploadAttachmentSerializer(
            data={**{'file': f}, **attrs}
        ) for f in files]
        for serializer in serializers:
            serializer.is_valid(raise_exception=True)
        return {'serializers': serializers}

    def create(self, validated_data):
        serializers = validated_data.pop('serializers')
        attachments = [
            serializer.save(**validated_data)
            for serializer in serializers
        ]
        return attachments


class AbstractTempSerializer(serializers.Serializer):

    def create(self, validated_data):
        storage_cls = get_storage_class()
        storage = storage_cls()
        storage.save(validated_data["filename"], validated_data["file"].file)
        return storage.url(validated_data["filename"])


class TempFileSerializer(AbstractTempSerializer):
    file = serializers.FileField()

    def validate(self, attrs):
        request = self.context['request']
        filename = upload_temp_user_file_to(
            user=request.user,
            filename=attrs['file'].name,
            error_field='file'
        )
        return {'file': attrs['file'], "filename": filename}


class TempImageSerializer(AbstractTempSerializer):
    image = ImageField()

    def validate(self, attrs):
        request = self.context['request']
        image_name = upload_temp_user_image_to(
            user=request.user,
            filename=attrs['image'].name,
            error_field='image'
        )
        return {'file': attrs['image'], "filename": image_name}
