from django.contrib.contenttypes.models import ContentType
from django.db import models

from greenbudget.lib.django_utils.query import PrePKBulkCreateQuerySet
from greenbudget.app.budgeting.query import BudgetAncestorQuerier


class GroupQuerier(BudgetAncestorQuerier):
    def for_budgets(self):
        from greenbudget.app.account.models import BudgetAccount
        from greenbudget.app.budget.models import Budget
        from greenbudget.app.subaccount.models import BudgetSubAccount
        ctype_ids = [
            ContentType.objects.get_for_model(m).id
            for m in [BudgetAccount, Budget, BudgetSubAccount]
        ]
        return self.filter(content_type__id__in=ctype_ids)

    def for_templates(self):
        from greenbudget.app.account.models import TemplateAccount
        from greenbudget.app.template.models import Template
        from greenbudget.app.subaccount.models import TemplateSubAccount
        ctype_ids = [
            ContentType.objects.get_for_model(m).id
            for m in [TemplateAccount, Template, TemplateSubAccount]
        ]
        return self.filter(content_type__id__in=ctype_ids)


class GroupQuery(GroupQuerier, PrePKBulkCreateQuerySet):
    pass


class GroupManager(GroupQuerier, models.Manager):
    queryset_class = GroupQuery

    def get_queryset(self):
        return self.queryset_class(self.model)


class BudgetGroupManager(GroupManager):
    def get_queryset(self):
        return super().get_queryset().for_budgets()


class TemplateGroupManager(GroupManager):
    def get_queryset(self):
        return super().get_queryset().for_templates()
