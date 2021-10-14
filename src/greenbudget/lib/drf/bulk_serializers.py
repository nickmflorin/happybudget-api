from django.db import models
from rest_framework import serializers


def meta_factory(**attrs):
    class Meta:
        pass
    for k, v in attrs.items():
        if v is not None:
            setattr(Meta, k, v)
    return Meta


def create_model_or_basic_serializer(fields=None, model_cls=None,
        base_model_serializer_cls=None, base_serializer_cls=None):
    base_serializer_cls = base_serializer_cls or serializers.Serializer
    if model_cls is not None:
        base_serializer_cls = base_model_serializer_cls or serializers.ModelSerializer  # noqa

    class Serializer(base_serializer_cls):
        Meta = meta_factory(fields=fields, model=model_cls)

    return Serializer


def create_bulk_serializer(serializer_cls, model_cls=None, child_context=None,
        bulk_context_name='bulk_context', fields=None):
    fields = fields or ()
    base_serializer_cls = create_model_or_basic_serializer(
        fields=('data', ) + fields,
        model_cls=model_cls
    )

    class BulkSerializer(base_serializer_cls):
        data = serializer_cls(many=True, required=True, nested=True)

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # We need/want to provide the nested serializer with the same
            # context that this serializer receives.  DRF does not do that
            # by default.
            self.fields['data'].context.update(**self._child_context)

        @property
        def _child_context(self):
            context = {bulk_context_name: True}
            context.update(**self.context)
            if child_context is not None:
                context.update(**child_context)
            return context

    return BulkSerializer


def create_bulk_delete_serializer(child_cls, base_cls=None, filter_qs=None):
    base_serializer_cls = create_model_or_basic_serializer(
        fields=('ids', ),
        model_cls=base_cls
    )

    class BulkDeleteSerializer(base_serializer_cls):
        ids = serializers.PrimaryKeyRelatedField(
            required=True,
            queryset=child_cls.objects.filter(filter_qs or models.Q()),
            write_only=True,
            many=True
        )

    return BulkDeleteSerializer


def create_bulk_change_serializer(child_cls, serializer_cls, filter_qs=None):
    # We have to extend the default model's serializer class such that we make
    # the ID a required write only field.
    class BulkChangeSerializer(serializer_cls):
        id = serializers.PrimaryKeyRelatedField(
            required=True,
            queryset=child_cls.objects.filter(filter_qs or models.Q())
        )

    return BulkChangeSerializer


def create_bulk_update_serializer(child_cls, serializer_cls, base_cls=None,
        filter_qs=None, child_context=None):
    # The BulkChangeSerializer is independent of the base_cls model (if
    # provided) - it is solely pertinent to the child_cls model that we are
    # applying bulk changes to.
    bulk_change_serializer_cls = create_bulk_change_serializer(
        child_cls=child_cls,
        serializer_cls=serializer_cls,
        filter_qs=filter_qs,
    )

    base_serializer = create_bulk_serializer(
        model_cls=base_cls,
        serializer_cls=bulk_change_serializer_cls,
        child_context=child_context,
        bulk_context_name='bulk_update_context'
    )

    class BulkUpdateSerializer(base_serializer):

        def validate_data(self, data):
            grouped = {}
            for change in data:
                instance = change['id']
                del change['id']
                if instance.pk not in grouped:
                    grouped[instance.pk] = {
                        'instance': instance,
                        'change': change,
                    }
                else:
                    grouped[instance.pk] = {
                        'instance': grouped[instance.pk]['instance'],
                        'change': {**grouped[instance.pk]['change'], **change},
                    }
            return [(gp['instance'], gp['change']) for _, gp in grouped.items()]

    return BulkUpdateSerializer


def create_bulk_create_serializer(child_cls, serializer_cls, base_cls=None,
        child_context=None):
    base_serializer = create_bulk_serializer(
        model_cls=base_cls,
        serializer_cls=serializer_cls,
        child_context=child_context,
        bulk_context_name='bulk_create_context',
    )

    class BulkCreateSerializer(base_serializer):
        def perform_children_write(self, validated_data_array, **kwargs):
            children = []
            for validated_data in validated_data_array:
                child = self.create_child(**validated_data, **kwargs)
                children.append(child)
            return children

        def create_child(self, **validated_data):
            serializer = serializer_cls()
            return serializer.create(validated_data)

    return BulkCreateSerializer
