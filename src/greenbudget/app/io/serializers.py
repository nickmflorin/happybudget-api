import imghdr
import logging
import os

from django.core.files.storage import get_storage_class

from rest_framework import serializers

from .exceptions import FileError
from .models import Attachment
from .storages import using_s3_storage
from .utils import (
    parse_filename,
    parse_image_filename,
    upload_temp_user_image_to,
    upload_temp_user_file_to
)


logger = logging.getLogger('greenbudget')


class ImageFieldFileSerializer(serializers.Serializer):
    url = serializers.URLField(read_only=True)
    size = serializers.IntegerField(read_only=True)
    width = serializers.IntegerField(read_only=True)
    height = serializers.IntegerField(read_only=True)
    extension = serializers.SerializerMethodField()

    def get_extension(self, instance):
        # Note that imghdr uses the local file system, so it will look at the
        # file in the local file system.  This only works when we are in local
        # development, because we are using Django's FileSystemStorage.
        if using_s3_storage():
            try:
                return parse_image_filename(instance.name, strict=False)[1]
            except FileError as e:
                logger.error("Corrupted image name stored in AWS.", extra={
                    "name": instance.name,
                    "exception": e
                })
                return None
        return imghdr.what(instance.path)


class SimpleAttachmentSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(read_only=True)
    name = serializers.SerializerMethodField()
    extension = serializers.SerializerMethodField()
    url = serializers.URLField(read_only=True, source='file.url')

    class Meta:
        model = Attachment
        fields = ('id', 'name', 'extension', 'url')

    def get_extension(self, instance):
        # Note that imghdr uses the local file system, so it will look at the
        # file in the local file system.  This only works when we are in local
        # development, because we are using Django's FileSystemStorage.
        if using_s3_storage():
            try:
                return parse_filename(instance.file.name, strict=False)[1]
            except FileError as e:
                logger.error("Corrupted attachment name stored in AWS.", extra={
                    "name": instance.name,
                    "exception": e
                })
                return None
        return imghdr.what(instance.file.path)

    def get_name(self, instance):
        return os.path.basename(instance.file.name)


class AttachmentSerializer(SimpleAttachmentSerializer):
    size = serializers.IntegerField(read_only=True, source='file.size')

    class Meta(SimpleAttachmentSerializer.Meta):
        model = Attachment
        fields = SimpleAttachmentSerializer.Meta.fields + ('size', )


class UploadAttachmentSerializer(serializers.ModelSerializer):
    file = serializers.FileField()

    class Meta:
        model = Attachment
        fields = ('file', )

    def validate(self, attrs):
        parse_filename(attrs['file'].name)
        return attrs


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
            filename=attrs['file'].name
        )
        return {'file': attrs['file'], "filename": filename}


class TempImageSerializer(AbstractTempSerializer):
    image = serializers.ImageField()

    def validate(self, attrs):
        request = self.context['request']
        image_name = upload_temp_user_image_to(
            user=request.user,
            filename=attrs['image'].name
        )
        return {'file': attrs['image'], "filename": image_name}
