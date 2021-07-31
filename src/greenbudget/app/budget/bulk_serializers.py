import traceback

from django.db import models
from rest_framework import serializers, exceptions
from rest_framework.utils import model_meta

from greenbudget.app import signals


class AbstractBulkSerializer(serializers.ModelSerializer):
    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # We need/want to provide the nested serializer with the same
        # context that this serializer receives.  DRF does not do that
        # by default.
        self.fields['data'].context.update(**self._child_context)


def create_bulk_serializer(base_cls, child_serializer_cls, child_context=None,
        bulk_context_name='bulk_context'):

    class BulkSerializer(AbstractBulkSerializer):
        data = child_serializer_cls(many=True, required=False, nested=True)

        class Meta:
            model = base_cls
            fields = ('data', )

        @property
        def _child_context(self):
            context = {bulk_context_name: True}
            context.update(**self.context)
            if child_context is not None:
                context.update(**child_context)
            return context

    return BulkSerializer


def create_bulk_create_serializer(base_cls, child_cls, child_serializer_cls,
        child_context=None):

    base_serializer = create_bulk_serializer(
        base_cls=base_cls,
        child_serializer_cls=child_serializer_cls,
        child_context=child_context,
        bulk_context_name='bulk_create_context'
    )

    class BulkCreateSerializer(base_serializer):
        count = serializers.IntegerField(required=False)

        class Meta:
            model = base_cls
            fields = base_serializer.Meta.fields + ('count', )

        def validate(self, attrs):
            if ('data' not in attrs and 'count' not in attrs) \
                    or ('data' in attrs and 'count' in attrs):
                raise exceptions.ValidationError(
                    "Either the `data` or `count` parameters must be provided."
                )
            return attrs

        @signals.bulk_context
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

        def update(self, instance, validated_data):
            if 'data' in validated_data:
                children = self.perform_children_write(
                    [payload for payload in validated_data.pop('data')],
                    **validated_data
                )
            else:
                children = self.perform_children_write(
                    [{} for _ in range(validated_data.pop('count'))],
                    **validated_data
                )
            # We have to refresh the instance from the DB because of the changes
            # that might have occurred due to the signals.
            instance.refresh_from_db()
            return instance, children

    return BulkCreateSerializer


def create_bulk_delete_serializer(base_cls, child_cls, filter_qs=None):
    class BulkDeleteSerializer(serializers.ModelSerializer):
        ids = serializers.PrimaryKeyRelatedField(
            required=True,
            queryset=child_cls.objects.filter(filter_qs or models.Q()),
            write_only=True,
            many=True
        )

        class Meta:
            model = base_cls
            fields = ('ids', )

        def update(self, instance, validated_data):
            with signals.bulk_context:
                for child in validated_data['ids']:
                    child.delete()
            # We have to refresh the instance from the DB because of the changes
            # that might have occurred due to the signals.
            instance.refresh_from_db()
            return instance
    return BulkDeleteSerializer


def create_bulk_update_serializer(base_cls, child_cls, child_serializer_cls,
        filter_qs=None, child_context=None):

    class BulkChangeSerializer(child_serializer_cls):
        id = serializers.PrimaryKeyRelatedField(
            required=True,
            queryset=child_cls.objects.filter(filter_qs or models.Q())
        )

    base_serializer = create_bulk_serializer(
        base_cls=base_cls,
        child_serializer_cls=BulkChangeSerializer,
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

        def update(self, instance, validated_data):
            data = validated_data.pop('data', None)
            if data is not None:
                with signals.bulk_context:
                    for child, change in data:
                        # At this point, the change already represents the
                        # validated data for that specific serializer.  So we do
                        # not need to pass in the validated data on __init__
                        # and rerun validation.
                        serializer = child_serializer_cls(
                            partial=True, context=self._child_context)
                        serializer.update(child, {**validated_data, **change})
                # We have to refresh the instance from the DB because of the
                # changes that might have occurred due to the signals.
                instance.refresh_from_db()
            return instance

    return BulkUpdateSerializer
