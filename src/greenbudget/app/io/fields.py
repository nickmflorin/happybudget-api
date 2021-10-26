import base64
import logging
import imghdr
import uuid

from botocore import exceptions

from django.core.files.base import ContentFile

from rest_framework import serializers


logger = logging.getLogger('greenbudget')


class Base64ImageField(serializers.ImageField):
    """
    A :obj:`rest_framework.serializers.ImageField` field that allows image
    uploads via raw POST data.  It uses base64 for encoding/decoding the
    contents of the file.
    """

    def to_representation(self, instance):
        from .serializers import ImageFieldFileSerializer

        if instance is not None:
            try:
                return ImageFieldFileSerializer(instance).data
            except ValueError:
                # This can happen if the instance does not have a file
                # associated with it.
                return super().to_representation(instance)
            except exceptions.ClientError:
                # This can happen if there is an error retrieving the image from
                # AWS.  Common case would be a 404 error if we had an image
                # stored locally and we started using S3 in local dev mode.
                logger.exception("Could not find AWS image.")
                return super().to_representation(instance)
            except FileNotFoundError:
                # This can happen if there is an error retrieving the image from
                # local storage.  This happens a lot when switching between S3
                # and local storage in local development.
                logger.exception("Could not find image file locally.")
                return super().to_representation(instance)
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
                file_extension = self.get_file_extension(file_name, decoded_file)
                complete_file_name = "%s.%s" % (file_name, file_extension, )
                data = ContentFile(decoded_file, name=complete_file_name)

        return super(Base64ImageField, self).to_internal_value(data)

    def get_file_extension(self, file_name, decoded_file):
        extension = imghdr.what(file_name, decoded_file)
        return "jpg" if extension == "jpeg" else extension
