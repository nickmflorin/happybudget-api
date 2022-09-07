from django.contrib.contenttypes.models import ContentType

from happybudget.app.budgeting.query import BudgetAncestorQuerier
from happybudget.app.user.query import ModelOwnershipQuerier
from happybudget.app.tabling.query import RowQuerier, RowQuerySet


class GroupQuerier(RowQuerier, ModelOwnershipQuerier, BudgetAncestorQuerier):
    def for_budgets(self):
        # pylint: disable=import-outside-toplevel
        from happybudget.app.account.models import BudgetAccount
        from happybudget.app.budget.models import Budget
        from happybudget.app.subaccount.models import BudgetSubAccount
        ctype_ids = [
            ContentType.objects.get_for_model(m).id
            for m in [BudgetAccount, Budget, BudgetSubAccount]
        ]
        return self.filter(content_type__id__in=ctype_ids)

    def for_templates(self):
        # pylint: disable=import-outside-toplevel
        from happybudget.app.account.models import TemplateAccount
        from happybudget.app.template.models import Template
        from happybudget.app.subaccount.models import TemplateSubAccount
        ctype_ids = [
            ContentType.objects.get_for_model(m).id
            for m in [TemplateAccount, Template, TemplateSubAccount]
        ]
        return self.filter(content_type__id__in=ctype_ids)

    def empty(self):
        return self.filter(accounts=None, subaccounts=None)


class GroupQuerySet(RowQuerySet, GroupQuerier):
    pass
