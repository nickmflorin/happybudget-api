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


def create_model_or_basic_serializer(**kwargs):
    base_serializer_cls = serializers.Serializer
    if kwargs.get('model_cls') is not None:
        base_serializer_cls = serializers.ModelSerializer

    class Serializer(base_serializer_cls):
        Meta = meta_factory(
            fields=kwargs.get('fields', ()),
            model=kwargs.get('model_cls')
        )

    return Serializer


def create_bulk_serializer(child_cls, **kwargs):
    base_serializer_cls = create_model_or_basic_serializer(**kwargs)

    class BulkSerializer(base_serializer_cls):
        @property
        def _child_context(self):
            context = {self.bulk_context_name: True}
            context.update(**self.context)
            if kwargs.get('child_context') is not None:
                context.update(**kwargs.get('child_context'))
            return context

        @property
        def manager_method_name(self):
            raise NotImplementedError()

        @property
        def bulk_context_name(self):
            return "bulk_context"

        def _validate_manager(self):
            if not hasattr(child_cls.objects, self.manager_method_name):
                raise Exception(
                    'The manager for %s must define a `%s` method.'
                    % (child_cls.__name__, self.manager_method_name)
                )

        def save(self, **kwargs):
            # Applying the changes in the .save() method is only applicable when
            # not using a ModelSerializer.
            if isinstance(self, serializers.ModelSerializer):
                return super().save(**kwargs)
            self._validate_manager()
            return self.perform({**self.validated_data, **kwargs})

        def update(self, instance, validated_data):
            # Applying the changes in the .update() method is only applicable
            # when using a ModelSerializer.
            if not isinstance(self, serializers.ModelSerializer):
                return super().update(instance, validated_data)
            self._validate_manager()
            data = self.perform(validated_data)
            # We have to refresh the instance from the DB because of the changes
            # that might have occurred due to the signals.
            instance.refresh_from_db()
            if getattr(self, 'return_results', True):
                return instance, data
            return instance

    return BulkSerializer


def create_bulk_patch_post_serializer(serializer_cls, **kwargs):
    base_serializer_cls = create_bulk_serializer(
        fields=('data', ) + kwargs.get('fields', ()),
        **kwargs
    )

    class BulkSerializer(base_serializer_cls):
        data = serializer_cls(many=True, required=True, nested=True)

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # We need/want to provide the nested serializer with the same
            # context that this serializer receives.  DRF does not do that
            # by default.
            self.fields['data'].context.update(**self._child_context)

    return BulkSerializer


def create_bulk_delete_serializer(child_cls, **kwargs):
    base_serializer_cls = create_bulk_serializer(
        fields=('ids', ),
        child_cls=child_cls,
        **kwargs
    )

    filter_qs = kwargs.get('filter_qs', models.Q())

    class BulkDeleteSerializer(base_serializer_cls):
        manager_method_name = 'bulk_delete'
        return_results = False

        ids = serializers.PrimaryKeyRelatedField(
            required=True,
            queryset=child_cls.objects.filter(filter_qs),
            write_only=True,
            many=True
        )

        def perform(self, validated_data):
            if not hasattr(child_cls.objects, 'bulk_delete'):
                raise Exception(
                    'The manager for %s must define a `%s` method.'
                    % (child_cls.__name__, 'bulk_delete')
                )
            return child_cls.objects.bulk_delete(validated_data['ids'])

    return BulkDeleteSerializer


def create_bulk_change_serializer(serializer_cls, **kwargs):
    # We have to extend the default model's serializer class such that we make
    # the ID a required write only field.
    filter_qs = kwargs.get('filter_qs', models.Q())

    class BulkChangeSerializer(serializer_cls):
        id = serializers.PrimaryKeyRelatedField(
            required=True,
            queryset=serializer_cls.Meta.model.objects.filter(filter_qs)
        )

    return BulkChangeSerializer


def create_bulk_update_serializer(serializer_cls, **kwargs):
    # The BulkChangeSerializer is independent of the base_cls model (if
    # provided) - it is solely pertinent to the child_cls model that we are
    # applying bulk changes to.
    bulk_change_serializer_cls = create_bulk_change_serializer(
        serializer_cls=serializer_cls,
        **kwargs
    )

    base_serializer = create_bulk_patch_post_serializer(
        serializer_cls=bulk_change_serializer_cls,
        child_cls=serializer_cls.Meta.model,
        **kwargs
    )

    ModelClass = serializer_cls.Meta.model

    class BulkUpdateSerializer(base_serializer):
        manager_method_name = 'bulk_save'
        bulk_context_name = 'bulk_update_context'

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

        def child_serializer_update(self, serializer, instance, validated_data):
            """
            An adapted version of Django REST Framework's
            :obj:`serializers.ModelSerializer` update method that applies the
            updates to the model instances without saving them, so they can
            be updated in a single batch.
            """
            m2m_fields_to_set = []

            serializers.raise_errors_on_nested_writes(
                'update', serializer, validated_data)
            info = model_meta.get_field_info(instance)

            # Simply set each attribute on the instance, and then save it.
            # Note that unlike `.create()` we don't need to treat many-to-many
            # relationships as being a special case. During updates we already
            # have an instance pk for the relationships to be associated with.
            m2m_fields = []
            fields = []

            for attr, value in validated_data.items():
                if attr in info.relations and info.relations[attr].to_many:
                    m2m_fields.append((attr, value))
                else:
                    fields.append(attr)
                    setattr(instance, attr, value)

            # Keep track of the m2m fields that we need to save after all of the
            # instances are updated.
            for attr, value in m2m_fields:
                field = getattr(instance, attr)
                m2m_fields_to_set.append((field, value))

            return instance, m2m_fields_to_set, fields

        def perform(self, validated_data):
            children = []
            m2m_fields_to_set = []
            update_fields = set([])

            for child, change in validated_data.pop('data', []):
                # At this point, the change already represents the validated
                # data for that specific serializer.  So we do not need to
                # pass in the validated data on __init__ and rerun the
                # validation routines.
                serializer = serializer_cls(
                    partial=True,
                    context=self._child_context
                )
                updated_child, m2m, fields = self.child_serializer_update(
                    serializer=serializer,
                    instance=child,
                    validated_data={**validated_data, **change}
                )
                children.append(updated_child)
                m2m_fields_to_set.extend(m2m)
                update_fields.update(fields)

            if not hasattr(ModelClass.objects, 'bulk_save'):
                raise Exception(
                    'The manager for %s must define a `%s` method.'
                    % (ModelClass.__name__, 'bulk_save')
                )

            # It is possible that the bulk update only applies to M2M fields,
            # in which case there will be no `update_fields` and we do not need
            # to apply the bulk save.
            if update_fields:
                ModelClass.objects.bulk_save(children, update_fields)

            # Note that many-to-many fields are set after updating instance.
            # Setting m2m fields triggers signals which could potentially change
            # updated instance and we do not want it to collide with .update()
            for field, value in m2m_fields_to_set:
                field.set(value)

            return children

    return BulkUpdateSerializer


def create_bulk_create_serializer(serializer_cls, **kwargs):
    ModelClass = serializer_cls.Meta.model

    base_serializer = create_bulk_patch_post_serializer(
        serializer_cls=serializer_cls,
        child_cls=ModelClass,
        **kwargs
    )

    class BulkCreateSerializer(base_serializer):
        manager_method_name = 'bulk_add'
        bulk_context_name = 'bulk_create_context'

        def child_serializer_create(self, serializer, validated_data):
            """
            An adapted version of Django REST Framework's
            :obj:`serializers.ModelSerializer` create method that instantiates
            the model instances without creating them, so they can all be
            created in a single batch.
            """
            serializers.raise_errors_on_nested_writes(
                'create', serializer, validated_data)

            # Keep track of the m2m fields that we need to save after all of the
            # instances are created.
            info = model_meta.get_field_info(ModelClass)
            many_to_many = {}
            for field_name, relation_info in info.relations.items():
                if relation_info.to_many and (field_name in validated_data):
                    many_to_many[field_name] = validated_data.pop(field_name)

            # Note: Here, instead of applying .create() like DRF does, we
            # simply instantiate the object.
            instance = ModelClass(**validated_data)

            return instance, many_to_many

        def perform(self, validated_data):
            children = []
            m2m_fields = []

            # Instantiate the model instances for each set of data in the
            # overall data set.
            data = validated_data.pop('data')

            for model_data in data:
                # At this point, the change already represents the validated
                # data for that specific serializer.  So we do not need to
                # pass in the validated data on __init__ and rerun the
                # validation routines.
                serializer = serializer_cls(context=self._child_context)
                instantiated_child, m2m = self.child_serializer_create(
                    serializer=serializer,
                    validated_data={**validated_data, **model_data}
                )
                children.append(instantiated_child)
                m2m_fields.append(m2m)

            # We have to create the instances in a bulk/batch operation before
            # we can attribute the M2M fields to those instances.  Unfortunately,
            # because an instance does not have an ID before it is created, the
            # only way to know what M2M field changes related to what instance
            # is the order of the M2M changes in the array and the order of the
            # associated instance in the array of created children.
            if not hasattr(ModelClass.objects, 'bulk_add'):
                raise Exception(
                    'The manager for %s must define a `%s` method.'
                    % (ModelClass.__name__, 'bulk_add')
                )

            created = ModelClass.objects.bulk_add(children)
            assert len(created) == len(m2m_fields)

            # Note that many-to-many fields are set after updating instance.
            # Setting m2m fields triggers signals which could potentially change
            # updated instance and we do not want it to collide with .update()
            for i, child in enumerate(created):
                m2m_fields_to_set = [
                    (getattr(child, field_name), value)
                    for field_name, value in m2m_fields[i].items()
                ]
                for field, value in m2m_fields_to_set:
                    field.set(value)
            return created

    return BulkCreateSerializer
