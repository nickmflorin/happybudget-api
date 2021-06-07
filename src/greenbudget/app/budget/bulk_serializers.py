from django.db import transaction, models
from rest_framework import serializers, exceptions


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

        def perform_children_write(self, validated_data_array, **kwargs):
            children = []
            with transaction.atomic():
                for validated_data in validated_data_array:
                    child = child_cls.objects.create(**validated_data, **kwargs)
                    children.append(child)
            return children

        def update(self, instance, validated_data):
            if 'data' in validated_data:
                return self.perform_children_write(
                    [payload for payload in validated_data.pop('data')],
                    **validated_data
                )
            return self.perform_children_write(
                [{} for _ in range(validated_data.pop('count'))],
                **validated_data
            )

    return BulkCreateSerializer


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
            with transaction.atomic():
                for child, change in validated_data.pop('data'):
                    serializer = child_serializer_cls(
                        instance=child,
                        data=change,
                        partial=True,
                        context=self._child_context
                    )
                    serializer.is_valid(raise_exception=True)
                    serializer.save(**validated_data)
            return instance

    return BulkUpdateSerializer
