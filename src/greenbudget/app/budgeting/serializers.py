from greenbudget.lib.drf.bulk_serializers import (
    create_bulk_create_serializer as create_generic_bulk_create_serializer,
    create_bulk_update_serializer as create_generic_bulk_update_serializer,
    create_bulk_delete_serializer as create_generic_bulk_delete_serializer
)
from greenbudget.lib.drf.serializers import (
    PolymorphicNonPolymorphicSerializer,
    ModelSerializer
)

from greenbudget.app import signals
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


def create_bulk_create_serializer(base_cls, child_cls, child_serializer_cls,
        child_context=None):
    generic_serializer_cls = create_generic_bulk_create_serializer(
        base_cls=base_cls,
        child_context=child_context,
        serializer_cls=child_serializer_cls,
        child_cls=child_cls
    )

    class BulkCreateSerializer(generic_serializer_cls):
        def update(self, instance, validated_data):
            with signals.bulk_context:
                children = self.perform_children_write(
                    [payload for payload in validated_data.pop('data')],
                    **validated_data
                )
            # We have to refresh the instance from the DB because of the changes
            # that might have occurred due to the signals.
            instance.refresh_from_db()
            return instance, children

    return BulkCreateSerializer


def create_bulk_delete_serializer(base_cls, child_cls, filter_qs=None):
    generic_serializer_cls = create_generic_bulk_delete_serializer(
        base_cls=base_cls,
        child_cls=child_cls,
        filter_qs=filter_qs
    )

    class BulkDeleteSerializer(generic_serializer_cls):
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
    generic_serializer_cls = create_generic_bulk_update_serializer(
        child_cls=child_cls,
        base_cls=base_cls,
        filter_qs=filter_qs,
        child_context=child_context,
        serializer_cls=child_serializer_cls
    )

    class BulkUpdateSerializer(generic_serializer_cls):
        def update(self, instance, validated_data):
            data = validated_data.pop('data', [])
            children = []
            with signals.bulk_context:
                for child, change in data:
                    # At this point, the change already represents the
                    # validated data for that specific serializer.  So we do
                    # not need to pass in the validated data on __init__
                    # and rerun validation.
                    serializer = child_serializer_cls(
                        partial=True, context=self._child_context)
                    serializer.update(child, {**validated_data, **change})
                    children.append(child)
            # We have to refresh the instance from the DB because of the
            # changes that might have occurred due to the signals.
            instance.refresh_from_db()
            return instance, children

    return BulkUpdateSerializer
