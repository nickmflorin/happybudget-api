import traceback

from django.db import models
from rest_framework import serializers
from rest_framework.utils import model_meta


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
        data = serializer_cls(many=True, required=False, nested=True)

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
            """
            Analogous to Django REST Framework's
            `rest_framework.serializers.ModelSerializer.create` method, with
            the exception that it operates on the child class instead of the
            base model class.  This is because this serializer is in regard
            to updating the base model class - since bulk create operations
            happen with PATCH requests to the base model.

            Reference:
            ---------
            https://github.com/encode/django-rest-framework/blob/master/
                rest_framework/serializers.py#L904

            This method is essentially just:
                return ExampleModel.objects.create(**validated_data)
            with the handling of M2M fields.
            """
            if base_cls is not None:
                serializers.raise_errors_on_nested_writes(
                    'create', self, validated_data)

            # Remove many-to-many relationships from validated_data.
            # They are not valid arguments to the default `.create()` method,
            # as they require that the instance has already been saved.
            info = model_meta.get_field_info(child_cls)
            many_to_many = {}
            for field_name, relation_info in info.relations.items():
                if relation_info.to_many and (field_name in validated_data):
                    many_to_many[field_name] = validated_data.pop(field_name)

            try:
                instance = child_cls._default_manager.create(**validated_data)
            except TypeError:
                tb = traceback.format_exc()
                msg = (
                    'Got a `TypeError` when calling `%s.%s.create()`. '
                    'This may be because you have a writable field on the '
                    'serializer class that is not a valid argument to '
                    '`%s.%s.create()`. You may need to make the field '
                    'read-only, or override the %s.create() method to handle '
                    'this correctly.\nOriginal exception was:\n %s' %
                    (
                        child_cls.__name__,
                        child_cls._default_manager.name,
                        child_cls.__name__,
                        child_cls._default_manager.name,
                        self.__class__.__name__,
                        tb
                    )
                )
                raise TypeError(msg)

            # Save many-to-many relationships after the instance is created.
            if many_to_many:
                for field_name, value in many_to_many.items():
                    field = getattr(instance, field_name)
                    field.set(value)

            return instance

    return BulkCreateSerializer
