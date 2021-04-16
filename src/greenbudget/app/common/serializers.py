from rest_framework import serializers

from greenbudget.lib.rest_framework_utils.serializers import (
    PolymorphicNonPolymorphicSerializer)

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
            "greenbudget.app.budget.serializers.BaseBudgetSimpleSerializer",
            "budget"
        ),
        Template: (
            "greenbudget.app.budget.serializers.BaseBudgetSimpleSerializer",
            "template"
        )
    }


class AbstractBulkUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        abstract = True

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
