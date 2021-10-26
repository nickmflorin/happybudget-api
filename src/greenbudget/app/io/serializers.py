import imghdr
import os

from django.core.files.storage import get_storage_class

from rest_framework import serializers

from .models import Attachment
from .storages import using_s3_storage
from .utils import (
    parse_filename,
    parse_image_filename,
    upload_temp_user_image_to,
    upload_temp_user_file_to
)


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
            return parse_image_filename(instance.name, strict=False)[1]
        return imghdr.what(instance.path)


class SimpleAttachmentSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(read_only=True)
    name = serializers.SerializerMethodField()
    extension = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = ('id', 'name', 'extension')

    def get_extension(self, instance):
        # Note that imghdr uses the local file system, so it will look at the
        # file in the local file system.  This only works when we are in local
        # development, because we are using
        # django.core.files.storage.FileSystemStorage.  When we are are in
        # a production/dev environment, and we are using
        # storages.backends.s3boto3.S3Boto3Storage, we need to use an alternate
        # method to find the extension.
        if using_s3_storage():
            return parse_filename(instance.file.name, strict=False)[1]
        return imghdr.what(instance.file.path)

    def get_name(self, instance):
        return os.path.basename(instance.file.name)


class AttachmentSerializer(SimpleAttachmentSerializer):
    url = serializers.URLField(read_only=True, source='file.url')
    size = serializers.IntegerField(read_only=True, source='file.size')

    class Meta(SimpleAttachmentSerializer.Meta):
        model = Attachment
        fields = SimpleAttachmentSerializer.Meta.fields + ('size', 'url')


class UploadAttachmentSerializer(serializers.ModelSerializer):
    file = serializers.FileField()

    class Meta:
        model = Attachment
        fields = ('file', )

    def validate(self, attrs):
        parse_filename(attrs['file'].name)
        return attrs


class TempFileSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate(self, attrs):
        request = self.context['request']
        filename = upload_temp_user_file_to(
            user=request.user,
            filename=attrs['file'].name
        )
        return {'file': attrs['file'], "filename": filename}

    def create(self, validated_data):
        storage_cls = get_storage_class()
        storage = storage_cls()
        storage.save(validated_data["filename"], validated_data["file"].file)
        return storage.url(validated_data["filename"])


class TempImageSerializer(serializers.Serializer):
    image = serializers.ImageField()

    def validate(self, attrs):
        request = self.context['request']
        image_name = upload_temp_user_image_to(
            user=request.user,
            filename=attrs['image'].name
        )
        return {'image': attrs['image'], "image_name": image_name}

    def create(self, validated_data):
        storage_cls = get_storage_class()
        storage = storage_cls()
        storage.save(validated_data["image_name"], validated_data["image"].file)
        return storage.url(validated_data["image_name"])
