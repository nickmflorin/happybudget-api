from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import Color, ColorCodeValidator, Tag


class ColorField(serializers.RelatedField):
    """
    A :obj:`rest_framework.serializers.RelatedField` that behaves very
    similarly to :obj:`reset_framework.serializers.PrimaryKeyRelatedField` with
    the exception that the :obj:`Color` `code` field is used as the PK for
    read/write operations.
    """
    default_error_messages = {
        'invalid_type': _(
            'This code "{code}" is not a valid hexadecimal color code.'),
        'required': _('This field is required.'),
        'does_not_exist': _('Invalid code "{code}" - color does not exist.'),
        'incorrect_type': _(
            'Incorrect type. Expected str value, received {data_type}.'),
    }

    def __init__(self, *args, **kwargs):
        self._content_type_model = kwargs.pop('content_type_model')
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        return Color.objects.for_model(self._content_type_model)

    def to_internal_value(self, data):
        queryset = self.get_queryset()
        try:
            if isinstance(data, bool):
                raise TypeError
            try:
                ColorCodeValidator(data)
            except ValidationError:
                self.fail('invalid_type', code=data)
            return queryset.get(code=data)
        except Color.DoesNotExist:
            self.fail('does_not_exist', code=data)
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data).__name__)

    def to_representation(self, instance):
        return instance.code


class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color

    def to_representation(self, instance):
        return instance.code


class TagSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    title = serializers.CharField(read_only=True)
    order = serializers.IntegerField(read_only=True)

    class Meta:
        model = Tag
        fields = ('id', 'created_at', 'updated_at', 'title', 'order')


class TagField(serializers.PrimaryKeyRelatedField):
    """
    A :obj:`rest_framework.serializers.PrimaryKeyRelatedField` that renders
    the full serialized tag on read operations.
    """

    def __init__(self, *args, **kwargs):
        self._model_cls = kwargs.pop('model_cls', None)
        self._serializer_class = kwargs.pop('serializer_class', TagSerializer)
        super().__init__(*args, **kwargs)

    def to_representation(self, instance):
        if self.pk_field is not None:
            return super().to_representation(instance)
        queryset = self.get_queryset()
        # The queryset will be None when the field is being used as a read only.
        if queryset is not None:
            instance = queryset.get(pk=instance.pk)
            return self._serializer_class(instance).data
        elif self._model_cls is not None:
            instance = self._model_cls.objects.get(pk=instance.pk)
            return self._serializer_class(instance).data
        return super().to_representation(instance)
