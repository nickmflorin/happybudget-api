from greenbudget.lib.drf.bulk_serializers import (
    create_bulk_create_serializer as create_generic_bulk_create_serializer,
    create_bulk_update_serializer as create_generic_bulk_update_serializer,
    create_bulk_delete_serializer as create_generic_bulk_delete_serializer
)
from greenbudget.lib.drf.serializers import PolymorphicNonPolymorphicSerializer

from greenbudget.app import signals
from greenbudget.app.account.models import Account
from greenbudget.app.budget.models import Budget
from greenbudget.app.subaccount.models import SubAccount
from greenbudget.app.template.models import Template


class EntitySerializer(PolymorphicNonPolymorphicSerializer):
    choices = {
        Account: (
            "greenbudget.app.account.serializers.AccountSimpleSerializer",
            "account"
        ),
        SubAccount: (
            "greenbudget.app.subaccount.serializers.SubAccountSimpleSerializer",
            "subaccount"
        ),
        Budget: (
            "greenbudget.app.budget.serializers.BaseBudgetSerializer",
            "budget"
        ),
        Template: (
            "greenbudget.app.budget.serializers.BaseBudgetSerializer",
            "template"
        )
    }


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
