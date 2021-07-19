from rest_framework import serializers
from .serializers import TagSerializer


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
