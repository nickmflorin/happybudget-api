from rest_framework import serializers
from rest_framework.utils import model_meta

from greenbudget.lib.drf.bulk_serializers import (
    create_bulk_create_serializer as create_generic_bulk_create_serializer,
    create_bulk_update_serializer as create_generic_bulk_update_serializer,
    create_bulk_delete_serializer as create_generic_bulk_delete_serializer
)
from greenbudget.lib.drf.serializers import (
    PolymorphicNonPolymorphicSerializer,
    ModelSerializer
)

from greenbudget.app.account.models import (
    Account, BudgetAccount, TemplateAccount)
from greenbudget.app.budget.models import Budget
from greenbudget.app.subaccount.models import (
    SubAccount, BudgetSubAccount, TemplateSubAccount)
from greenbudget.app.template.models import Template


class SimpleEntityPolymorphicSerializer(PolymorphicNonPolymorphicSerializer):
    choices = {
        Account: "greenbudget.app.account.serializers.AccountSimpleSerializer",
        SubAccount: "greenbudget.app.subaccount.serializers.SubAccountSimpleSerializer",  # noqa
        Budget: "greenbudget.app.budget.serializers.BaseBudgetSerializer",
        Template: "greenbudget.app.budget.serializers.BaseBudgetSerializer",
    }


class EntityPolymorphicSerializer(PolymorphicNonPolymorphicSerializer):
    choices = {
        BudgetAccount: "greenbudget.app.account.serializers.BudgetAccountSerializer",  # noqa
        BudgetSubAccount: "greenbudget.app.subaccount.serializers.BudgetSubAccountSerializer",  # noqa
        TemplateAccount: "greenbudget.app.account.serializers.TemplateAccountSerializer",  # noqa
        TemplateSubAccount: "greenbudget.app.subaccount.serializers.TemplateSubAccountSerializer",  # noqa
        Budget: "greenbudget.app.budget.serializers.BudgetSerializer",
        Template: "greenbudget.app.template.serializers.TemplateSerializer",
    }


class BudgetParentContextSerializer(ModelSerializer):
    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        self._only_model = kwargs.pop('only_model', False)
        super().__init__(*args, **kwargs)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if self._only_model:
            return data
        if self.read_only is not True:
            if 'request' not in self.context:
                raise Exception(
                    "The request must be provided in context when using %s."
                    % self.__class__.__name__
                )

            if self.context['request'].method in ('POST', 'PATCH'):
                parent = instance.parent
                parent.refresh_from_db()
                if isinstance(parent, (Budget, Template)):
                    return {
                        "data": data,
                        "budget": EntityPolymorphicSerializer(
                            instance=parent).data
                    }
                else:
                    budget = instance.parent.budget
                    budget.refresh_from_db()
                    return {
                        "data": data,
                        "budget": EntityPolymorphicSerializer(
                            instance=budget).data,
                        "parent": EntityPolymorphicSerializer(
                            instance=parent).data,
                    }
        return data


def create_bulk_create_serializer(base_cls, child_serializer_cls,
        child_context=None):
    generic_serializer_cls = create_generic_bulk_create_serializer(
        base_cls=base_cls,
        child_context=child_context,
        serializer_cls=child_serializer_cls
    )

    ModelClass = child_serializer_cls.Meta.model

    class BulkCreateSerializer(generic_serializer_cls):
        def child_serializer_create(self, serializer, validated_data):
            """
            An adapted version of Django REST Framework's
            :obj:`serializers.ModelSerializer` create method that allows us
            to perform the changes to the model without saving the model
            immediately.  This is important because we want to perform the
            saves inside of the bulk context.
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

        def update(self, instance, validated_data):
            if not hasattr(ModelClass.objects, 'bulk_add'):
                raise Exception(
                    'The manager for %s must define a bulk add method.'
                    % ModelClass.__name__
                )

            children = []
            m2m_fields = []
            for data in validated_data.pop('data', []):
                # At this point, the change already represents the validated
                # data for that specific serializer.  So we do not need to
                # pass in the validated data on __init__ and rerun the
                # validation routines.
                serializer = child_serializer_cls(context=self._child_context)
                instantiated_child, m2m = self.child_serializer_create(
                    serializer=serializer,
                    validated_data={**validated_data, **data}
                )
                children.append(instantiated_child)
                m2m_fields.append(m2m)

            # We have to create the instances in a bulk/batch operation before
            # we can attribute the M2M fields to those instances.  Unfortunately,
            # because an instance does not have an ID before it is created, the
            # only way to know what M2M field changes related to what instance
            # is the order of the M2M changes in the array and the order of the
            # associated instance in the array of created children.
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

            # We have to refresh the instance from the DB because of the changes
            # due to the bulk save.
            instance.refresh_from_db()
            return instance, created

    return BulkCreateSerializer


def create_bulk_delete_serializer(base_cls, child_cls, filter_qs=None):
    generic_serializer_cls = create_generic_bulk_delete_serializer(
        base_cls=base_cls,
        child_cls=child_cls,
        filter_qs=filter_qs
    )

    class BulkDeleteSerializer(generic_serializer_cls):
        def update(self, instance, validated_data):
            if not hasattr(child_cls.objects, 'bulk_delete'):
                raise Exception(
                    'The manager for %s must define a bulk delete method.'
                    % child_cls.__name__
                )
            child_cls.objects.bulk_delete(validated_data['ids'])
            # We have to refresh the instance from the DB because of the changes
            # that might have occurred due to the signals.
            instance.refresh_from_db()
            return instance
    return BulkDeleteSerializer


def create_bulk_update_serializer(base_cls, child_serializer_cls, filter_qs=None,
        child_context=None):
    generic_serializer_cls = create_generic_bulk_update_serializer(
        base_cls=base_cls,
        filter_qs=filter_qs,
        child_context=child_context,
        serializer_cls=child_serializer_cls
    )

    ModelClass = child_serializer_cls.Meta.model

    class BulkUpdateSerializer(generic_serializer_cls):
        def child_serializer_update(self, serializer, instance, validated_data):
            """
            An adapted version of Django REST Framework's
            :obj:`serializers.ModelSerializer` update method that allows us
            to perform the changes to the model without saving the model
            immediately.  This is important because we want to perform the
            saves inside of the bulk context.
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

        def update(self, instance, validated_data):
            if not hasattr(ModelClass.objects, 'bulk_save'):
                raise Exception(
                    'The manager for %s must define a bulk save method.'
                    % ModelClass.__name__
                )
            children = []
            m2m_fields_to_set = []
            update_fields = set([])
            for child, change in validated_data.pop('data', []):
                # At this point, the change already represents the validated
                # data for that specific serializer.  So we do not need to
                # pass in the validated data on __init__ and rerun the
                # validation routines.
                serializer = child_serializer_cls(
                    partial=True,
                    context=self._child_context
                )
                updated_child, m2m, fields = self.child_serializer_update(  # noqa
                    serializer=serializer,
                    instance=child,
                    validated_data={**validated_data, **change}
                )
                children.append(updated_child)
                m2m_fields_to_set.extend(m2m)
                update_fields.update(fields)

            ModelClass.objects.bulk_save(children, update_fields)

            # Note that many-to-many fields are set after updating instance.
            # Setting m2m fields triggers signals which could potentially change
            # updated instance and we do not want it to collide with .update()
            for field, value in m2m_fields_to_set:
                field.set(value)

            # We have to refresh the instance from the DB because of the changes
            # due to the bulk save.
            instance.refresh_from_db()
            return instance, children

    return BulkUpdateSerializer
