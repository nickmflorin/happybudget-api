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
