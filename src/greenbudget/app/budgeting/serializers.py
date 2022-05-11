from happybudget.lib.drf.serializers import PolymorphicNonPolymorphicSerializer

from happybudget.app.account.models import (
    Account, BudgetAccount, TemplateAccount)
from happybudget.app.budget.models import Budget
from happybudget.app.serializers import ModelSerializer
from happybudget.app.subaccount.models import (
    SubAccount, BudgetSubAccount, TemplateSubAccount)
from happybudget.app.template.models import Template


class EntityAncestorSerializer(PolymorphicNonPolymorphicSerializer):
    choices = {
        Account: "happybudget.app.account.serializers.AccountSimpleSerializer",
        SubAccount: (
            "happybudget.app.subaccount.serializers.SubAccountSimpleSerializer"),
        Budget: "happybudget.app.budget.serializers.BaseBudgetSerializer",
        Template: "happybudget.app.budget.serializers.BaseBudgetSerializer",
    }


class EntityPolymorphicSerializer(PolymorphicNonPolymorphicSerializer):
    choices = {
        BudgetAccount: (
            "happybudget.app.account.serializers.BudgetAccountSerializer"),
        BudgetSubAccount: (
            "happybudget.app.subaccount.serializers.BudgetSubAccountSerializer"),
        TemplateAccount: (
            "happybudget.app.account.serializers.TemplateAccountSerializer"),
        TemplateSubAccount: (
            "happybudget.app.subaccount.serializers."
            "TemplateSubAccountSerializer"
        ),
        Budget: "happybudget.app.budget.serializers.BudgetSerializer",
        Template: "happybudget.app.template.serializers.TemplateSerializer",
    }


class AncestrySerializer(ModelSerializer):
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
            if self.request.method in ('POST', 'PATCH'):
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
