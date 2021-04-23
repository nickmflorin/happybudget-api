import base64
import imghdr
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers


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


class Base64ImageField(serializers.ImageField):
    """
    A :obj:`rest_framework.serializers.ImageField` field that allows image
    uploads via raw POST data.  It uses base64 for encoding/decoding the
    contents of the file.
    """

    def to_internal_value(self, data):
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
