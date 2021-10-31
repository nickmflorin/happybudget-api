from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


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
        except TypeError:
            self.fail('incorrect_type', data_type=type(data).__name__)
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
