from django.db import models
from rest_framework import serializers
from rest_framework.utils import model_meta

from .exceptions import RequiredFieldError


class SerializerMixin:
    @property
    def request(self):
        assert 'request' in self.context, \
            "The request must be provided in context when using the " \
            f"{self.__class__.__name__} serializer class."
        return self.context['request']

    @property
    def user(self):
        return self.request.user


class Serializer(SerializerMixin, serializers.Serializer):
    pass


class ModelSerializer(SerializerMixin, serializers.ModelSerializer):
    pass


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

    class _Serializer(base_serializer_cls):
        Meta = meta_factory(
            fields=kwargs.get('fields', ()),
            model=kwargs.get('model_cls')
        )

    return _Serializer


def create_bulk_serializer(**kwargs):
    base_serializer_cls = create_model_or_basic_serializer(**kwargs)
    # We need to have an awareness of what instance the changes are related to.
    # This can either be done by directly passing in the child class or by
    # passing in the serializer class which has the associated model in it's
    # Meta property.
    assert 'child_cls' in kwargs or 'serializer_cls' in kwargs, \
        "Either the child instance class or the serializer class must be " \
        "provided."

    if 'child_cls' in kwargs:
        child_cls = kwargs['child_cls']
    else:
        child_cls = kwargs['serializer_cls'].Meta.model

    class BulkSerializer(base_serializer_cls):
        bulk_context_name = 'bulk_context'

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

        def _validate_manager(self):
            if not hasattr(child_cls.objects, self.manager_method_name):
                raise Exception(
                    'The manager for %s must define a `%s` method.'
                    % (child_cls.__name__, self.manager_method_name)
                )

        def save(self, **kwargs):
            """
            Performs the base serializer class's save method in the case that
            the serializer is an instance of :obj:`serializers.ModelSerializer`,
            otherwise, performs the bulk operation.

            The serializer will be an instance of
            :obj:`serializers.ModelSerializer` only when the `model_cls`
            parameter is provided.  This `model_cls` parameter does not refer
            to the model that is being bulk updated, created or deleted - but
            rather the parent model that is changing as a result of a bulk
            update, create or delete.

            For instance, when bulk-updating a series of children for an
            :obj:`Account`, the endpoint is:

            PATCH /v1/accounts/<pk>/bulk-update-children/

            Here, the `model_cls` refers to the :obj:`Account` with the pk
            in the request path that we are updating the children of.

            Regardless of whether or not the serializer is a subclass of
            :obj:`serializers.ModelSerializer`, the validated data on the
            serializer will always be the data that is used to perform the
            bulk update, create or delete.

            The decision regarding how to apply that validated data to the
            children depends on whether or not the base serializer class is a
            subclass of :obj:`serializers.ModelSerializer`:

            - Is subclass of :obj:`serializers.ModelSerializer`
                1.  There is a parent model that the children are relative to.
                2.  The `.save()` method does not need to be overridden, because
                    the changes in the validated data will be applied in the
                    `update` method, due to the fact that we are updating the
                    parent model.
                3.  The `.update()` method needs to be overridden, in order to
                    apply the changes in the validated data to the children.

            - Is not subclass of :obj:`serializers.ModelSerializer`
                1.  There is no parent model that the children are relative to.
                2.  The `.save()` method needs to be overridden, since the
                    changes in the validated data will not be applied to the
                    children in the `update()` method since there is no parent
                    we are updating the children relative to.
                3.  The `update()` method does not need to be overridden, since
                    we are not updating the children relative to a parent model.
            """
            # Applying the changes in the .save() method is only applicable when
            # not using a ModelSerializer.
            if isinstance(self, serializers.ModelSerializer):
                return super().save(**kwargs)
            # There is no parent model that the children are relative to, so
            # we need to perform the bulk operation in the `.save()` method
            # (since the `.update()` method will not be called).
            self._validate_manager()
            return self.perform({**self.validated_data, **kwargs})

        def update(self, instance, validated_data):
            # Applying the changes in the .update() method is only applicable
            # when using a ModelSerializer.
            if not isinstance(self, serializers.ModelSerializer):
                return super().update(instance, validated_data)
            # There is a parent model that the children are relative to, so we
            # need to perform the bulk operation in the `.update()` method.
            self._validate_manager()
            data = self.perform(validated_data)
            # We have to refresh the instance from the DB because of the changes
            # that might have occurred due to the signals.
            instance.refresh_from_db()
            if getattr(self, 'return_results', True):
                return instance, data
            return instance

    return BulkSerializer


class BulkSerializerDataPrimaryKeyField(serializers.PrimaryKeyRelatedField):
    """
    An extension of :obj:`rest_framework.serializers.PrimaryKeyRelatedField`
    that is designed to handle dictionary objects with an `id` field instead of
    the integer ID directly.

    For example, typically with a PrimaryKeyRelatedField field we would do the
    following:

    >>> class ExampleSerializer(serializers.ModelSerializer):
    >>>     related_obj = serializers.PrimaryKeyRelatedField(...)

    Then, a PATCH or POST request might look like the following:

    >>> POST /v1/examples/ { related_obj: 5 }

    However, this does not work for the case of bulk updating a series of
    instances.  When we bulk update a series of instances, the data that is
    supplied in the PATCH request is an array that looks like the following:

    >>> [{id: 5, name: "New Name"}, {id: 6, name: "Second New Name", qty: 5}]

    This field needs to be able to operate on each object in the array, using
    the `id` field to perform the regular lookup internal to
    :obj:`rest_framework.serializers.PrimaryKeyRelatedField` and return the
    instance associated with that ID in addition to the supplementary data in
    the object.

    Note:
    ----
    The supplementary data provided for each instance will be validated later
    on, in accordance with the serializer applicable for that object data.
    """
    def to_internal_value(self, data):
        if 'id' not in data:
            raise RequiredFieldError("id")
        instance_id = data.pop('id')
        return super().to_internal_value(instance_id), data


def create_bulk_delete_serializer(child_cls, **kwargs):
    base_serializer_cls = create_bulk_serializer(
        fields=('ids', ),
        child_cls=child_cls,
        **kwargs
    )
    filter_qs = kwargs.get('filter_qs', models.Q())

    class BulkDeleteSerializer(base_serializer_cls):
        manager_method_name = 'bulk_delete'
        bulk_context_name = 'bulk_delete_context'
        return_results = False

        ids = serializers.PrimaryKeyRelatedField(
            required=True,
            queryset=child_cls.objects.filter(filter_qs),
            write_only=True,
            many=True
        )

        def perform(self, validated_data):
            # Exception should have already been raised at this point.
            assert hasattr(child_cls.objects, 'bulk_delete')
            return child_cls.objects.bulk_delete(
                validated_data['ids'],
                request=self.context['request']
            )

    return BulkDeleteSerializer


def create_bulk_update_serializer(serializer_cls, **kwargs):
    """
    Creates a serializer that has a `data` field, which is used to serialize
    the request data in the case of a bulk-update operation.

    In a bulk-update operation, the `data` in the request body will be an
    array of objects, each of which has an ID (referring to the model that
    needs to be updated) and the supplementary data that needs to be applied
    to the model during update:

    POST /v1/budgets/<pk>/bulk-update-children/
        {"data": [{"id": 4, "identifier": "1000"}]}

    Note that we do not want to use an array of nested serializers to represent
    the `data` field.  This is because when we are updating via a serializer,
    the serializer class needs to be initialized with the instance being updated
    in order to properly perform validation - but the instance is not yet
    available at the time the serializer is initialized.

    Usage of the :obj:`BulkSerializerDataPrimaryKeyField` allows us to convert
    the ID in each object of the `data` array to it's corresponding model
    without validating the supplementary data - which is something that is done
    by initializing the child (or nested) serializer class with the model
    instance in the `.perform()` method here.

    Note that this differs from the bulk-create case, as in a POST request
    we are not initializing any child serializer with an instance that already
    exists - so we can use the nested serializer approach.
    """
    filter_qs = kwargs.get('filter_qs', models.Q())
    ModelClass = serializer_cls.Meta.model

    # The BulkUpdateChildSerializer is independent of the base_cls model (if
    # provided) - it is solely pertinent to the child_cls model that we are
    # applying bulk changes to.
    class BulkUpdateChildSerializer(serializer_cls):
        # We have to extend the default model's serializer class such that we
        # make the ID a required write only field.
        id = serializers.PrimaryKeyRelatedField(
            required=True,
            queryset=serializer_cls.Meta.model.objects.filter(filter_qs)
        )

    base_serializer_cls = create_bulk_serializer(
        fields=('data', ) + kwargs.get('fields', ()),
        serializer_cls=BulkUpdateChildSerializer,
        **kwargs
    )

    class BulkUpdateSerializer(base_serializer_cls):
        manager_method_name = 'bulk_save'
        bulk_context_name = 'bulk_update_context'

        data = BulkSerializerDataPrimaryKeyField(
            many=True,
            required=True,
            queryset=serializer_cls.Meta.model.objects.filter(filter_qs),
        )

        def validate_data(self, data):
            """
            Does not actually perform validation, but simply groups the array
            of instances and associated changes such that the changes are
            grouped by instance.
            """
            grouped = {}
            for instance, attrs in data:
                if instance.pk not in grouped:
                    grouped[instance.pk] = {
                        'instance': instance,
                        'attrs': attrs,
                    }
                else:
                    grouped[instance.pk] = {
                        'instance': grouped[instance.pk]['instance'],
                        'attrs': {**grouped[instance.pk]['attrs'], **attrs},
                    }
            return [(gp['instance'], gp['attrs']) for _, gp in grouped.items()]

        def child_serializer_update(self, serializer, validated_data):
            """
            An adapted version of Django REST Framework's
            :obj:`serializers.ModelSerializer` update method that applies the
            updates to the model instances without saving them, so they can
            be updated in a single batch.
            """
            m2m_fields_to_set = []

            serializers.raise_errors_on_nested_writes(
                'update', serializer, validated_data)
            info = model_meta.get_field_info(serializer.instance)

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
                    setattr(serializer.instance, attr, value)

            # Keep track of the m2m fields that we need to save after all of the
            # instances are updated.
            for attr, value in m2m_fields:
                field = getattr(serializer.instance, attr)
                m2m_fields_to_set.append((field, value))

            return serializer.instance, m2m_fields_to_set, fields

        def perform(self, validated_data):
            children = []
            m2m_fields_to_set = []
            update_fields = set([])

            for instance, attrs in validated_data.pop('data', []):
                # The base serializer does not reference the child serializer
                # class directly as a nested field (as it does in the POST case
                # ). This means that the data associated with each instance has
                # not yet been validated.
                serializer = serializer_cls(
                    partial=True,
                    context=self._child_context,
                    instance=instance,
                    data=attrs
                )
                # Now it is safe to perform the serializer validation because
                # it has been provided with the instance we are updating.
                serializer.is_valid(raise_exception=True)
                updated_child, m2m, fields = self.child_serializer_update(
                    serializer=serializer,
                    validated_data={
                        **validated_data, **serializer.validated_data}
                )
                children.append(updated_child)
                m2m_fields_to_set.extend(m2m)
                update_fields.update(fields)

            # Exception should have already been raised at this point.
            assert hasattr(ModelClass.objects, self.manager_method_name)

            # It is possible that the bulk update only applies to M2M fields,
            # in which case there will be no `update_fields` and we do not need
            # to apply the bulk save.
            if update_fields:
                ModelClass.objects.bulk_save(
                    children, update_fields, request=self.context['request'])

            # Note that many-to-many fields are set after updating instance.
            # Setting m2m fields triggers signals which could potentially change
            # updated instance and we do not want it to collide with .update()
            for field, value in m2m_fields_to_set:
                field.set(value)

            return children

    return BulkUpdateSerializer


def create_bulk_create_serializer(serializer_cls, **kwargs):
    """
    Creates a serializer that has a `data` field, which is used to serialize
    the request data in the case of a bulk-create operation.

    In a bulk-create operation, the `data` in the request body will be an
    array of objects, each of which has the data that needs to be used to create
    the individual child.

    POST /v1/budgets/<pk>/bulk-create-children/
        {"data": [{"identifier": "1000"}, {"identifier": "2000"}]}

    Note that unlike the bulk-update case, we can in fact use an array of
    nested serializers to represent the `data` field - because we do not need
    to provide the nested serializers with an instance in order to properly
    perform validation, as the instance is not applicable when creating new
    instances.
    """
    ModelClass = serializer_cls.Meta.model

    base_serializer_cls = create_bulk_serializer(
        fields=('data', ) + kwargs.get('fields', ()),
        serializer_cls=serializer_cls,
        **kwargs
    )

    class BulkCreateSerializer(base_serializer_cls):
        manager_method_name = 'bulk_add'
        bulk_context_name = 'bulk_create_context'

        # Unlike the PATCH case, we simply use the child serializer class
        # directly as a nested serializer - since we do not have to worry about
        # providing each nested serializer an instance as we are not updating
        # the children, but creating them.
        data = serializer_cls(many=True, required=True)

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # We need/want to provide the nested serializer with the same
            # context that this serializer receives.  DRF does not do that
            # by default.
            self.fields['data'].context.update(**self._child_context)

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

            # The validated data consists of a series of key-value pairs that
            # should apply to all created models with the exception of the
            # `data` key, which is an array where each element applies to only
            # one model we are creating.  There are edge cases where the `data`
            # argument will not be in the validated_data, which usually happens
            # if the request payload isn't serialized properly.
            data = validated_data.pop('data', [])

            # Instantiate the model instances for each set of data in the
            # overall data set.
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

            # Exception should have already been raised at this point.
            assert hasattr(ModelClass.objects, self.manager_method_name)

            # We have to create the instances in a bulk/batch operation before
            # we can attribute the M2M fields to those instances.  Unfortunately,
            # because an instance does not have an ID before it is created, the
            # only way to know what M2M field changes related to what instance
            # is the order of the M2M changes in the array and the order of the
            # associated instance in the array of created children.
            created = ModelClass.objects.bulk_add(
                children, request=self.context['request'])
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
