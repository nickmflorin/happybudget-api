from rest_framework import serializers
from greenbudget.lib.drf.serializers import PolymorphicNonPolymorphicSerializer

from greenbudget.app.account.models import (
    Account, BudgetAccount, TemplateAccount)
from greenbudget.app.budget.models import Budget
from greenbudget.app.subaccount.models import (
    SubAccount, BudgetSubAccount, TemplateSubAccount)
from greenbudget.app.template.models import Template


class EntityAncestorSerializer(PolymorphicNonPolymorphicSerializer):
    choices = {
        Account: "greenbudget.app.account.serializers.AccountSimpleSerializer",
        SubAccount: (
            "greenbudget.app.subaccount.serializers.SubAccountSimpleSerializer"),
        Budget: "greenbudget.app.budget.serializers.BaseBudgetSerializer",
        Template: "greenbudget.app.budget.serializers.BaseBudgetSerializer",
    }


class EntityPolymorphicSerializer(PolymorphicNonPolymorphicSerializer):
    choices = {
        BudgetAccount: (
            "greenbudget.app.account.serializers.BudgetAccountSerializer"),
        BudgetSubAccount: (
            "greenbudget.app.subaccount.serializers.BudgetSubAccountSerializer"),
        TemplateAccount: (
            "greenbudget.app.account.serializers.TemplateAccountSerializer"),
        TemplateSubAccount: (
            "greenbudget.app.subaccount.serializers."
            "TemplateSubAccountSerializer"
        ),
        Budget: "greenbudget.app.budget.serializers.BudgetSerializer",
        Template: "greenbudget.app.template.serializers.TemplateSerializer",
    }


class AncestrySerializer(serializers.ModelSerializer):
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
                        "parent": EntityPolymorphicSerializer(
                            instance=parent,
                            context=self.context
                        ).data
                    }
                else:
                    budget = instance.parent.budget
                    budget.refresh_from_db()
                    return {
                        "data": data,
                        "budget": EntityPolymorphicSerializer(
                            instance=budget,
                            context=self.context
                        ).data,
                        "parent": EntityPolymorphicSerializer(
                            instance=parent,
                            context=self.context
                        ).data,
                    }
        return data
