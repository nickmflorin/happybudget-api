from django.db import models, IntegrityError

from greenbudget.app import signals
from greenbudget.app.budget.models import BaseBudget, Budget
from greenbudget.app.budget.duplication import BudgetDeriver

from .managers import TemplateManager


@signals.model()
class Template(BaseBudget):
    domain = "template"

    community = models.BooleanField(default=False)
    hidden = models.BooleanField(default=False)
    objects = TemplateManager()

    FIELDS_TO_DUPLICATE = BaseBudget.FIELDS_TO_DUPLICATE
    FIELDS_TO_DERIVE = ('image', 'name')
    CALCULATED_FIELDS = Budget.CALCULATED_FIELDS
    ESTIMATED_FIELDS = Budget.ESTIMATED_FIELDS

    associated = [
        ('template', 'template'),
        ('account', 'templateaccount'),
        ('subaccount', 'templatesubaccount')
    ]

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

    def derive(self, user, **kwargs):
        deriver = BudgetDeriver(self, user)
        return deriver.derive(**kwargs)

    def save(self, *args, **kwargs):
        if self.community is True and not self.created_by.is_staff:
            raise IntegrityError(
                "Community templates can only be created by staff users.")
        return super().save(*args, **kwargs)
