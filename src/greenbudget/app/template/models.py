from django.db import models, IntegrityError

from greenbudget.app import model
from greenbudget.app.budget.models import BaseBudget
from greenbudget.app.budgeting.models import AssociatedModel

from .managers import TemplateManager


@model.model(type='budget')
class Template(BaseBudget):
    community = models.BooleanField(default=False)
    hidden = models.BooleanField(default=False)
    objects = TemplateManager()

    budget_cls = AssociatedModel('template', 'template')
    account_cls = AssociatedModel('account', 'templateaccount')
    subaccount_cls = AssociatedModel('subaccount', 'templatesubaccount')

    domain = "template"

    class Meta(BaseBudget.Meta):
        verbose_name = "Template"
        verbose_name_plural = "Templates"
        # Check constraint to ensure that only community templates can be
        # hidden.
        constraints = [models.CheckConstraint(
            name="%(app_label)s_%(class)s_hidden_only_for_community",
            check=(
                models.Q(community=True, hidden=False)
                | models.Q(community=True, hidden=True)
                | models.Q(community=False, hidden=False)
            )
        )]

    def __str__(self):
        return self.name

    def validate_before_save(self, *args, **kwargs):
        if self.community is True and not self.created_by.is_staff:
            raise IntegrityError(
                "Community templates can only be created by staff users.")
