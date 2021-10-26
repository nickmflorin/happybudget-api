import imghdr
from django.core.files.storage import get_storage_class

from rest_framework import serializers

from .storages import using_s3_storage
from .utils import (
    get_image_filename_extension,
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
            extension = get_image_filename_extension(instance.name)
        else:
            extension = imghdr.what(instance.path)
        return "jpg" if extension == "jpeg" else extension


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
