from django.db import models

from greenbudget.app import signals
from greenbudget.app.budget.models import BaseBudget, Budget
from greenbudget.app.budgeting.models import AssociatedModel

from .managers import TemplateManager


@signals.model()
class Template(BaseBudget):
    domain = "template"

    community = models.BooleanField(default=False)
    hidden = models.BooleanField(default=False)
    objects = TemplateManager()

    CALCULATED_FIELDS = Budget.CALCULATED_FIELDS
    ESTIMATED_FIELDS = Budget.ESTIMATED_FIELDS

    budget_cls = AssociatedModel('template', 'template')
    account_cls = AssociatedModel('account', 'templateaccount')
    subaccount_cls = AssociatedModel('subaccount', 'templatesubaccount')

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
        return "Template: %s" % self.name
