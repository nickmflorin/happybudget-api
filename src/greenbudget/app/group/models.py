from django.db.utils import IntegrityError

from greenbudget.app import signals

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


@signals.model('suppress_budget_update')
class Group(models.Model):
    type = "group"
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        to='user.User',
        related_name='created_groups_new',
        on_delete=models.CASCADE,
        editable=False
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        to='user.User',
        related_name='updated_groups_new',
        on_delete=models.CASCADE,
        editable=False
    )
    name = models.CharField(max_length=128)
    color = models.ForeignKey(
        to='tagging.Color',
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to=models.Q(
            content_types__model='group',
            content_types__app_label='group'
        )
    )
    markups = models.ManyToManyField(
        to='markup.Markup',
        related_name='groups'
    )
    content_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.CASCADE,
        limit_choices_to=models.Q(app_label='subaccount', model='subaccount')
        | models.Q(app_label='account', model='account')
        | models.Q(app_label='budget', model='basebudget')
    )
    object_id = models.PositiveIntegerField(db_index=True)
    parent = GenericForeignKey('content_type', 'object_id')

    FIELDS_TO_DUPLICATE = ("name", "color")
    FIELDS_TO_DERIVE = ("name", "color")

    class Meta:
        get_latest_by = "created_at"
        ordering = ('created_at', )
        verbose_name = "Group"
        verbose_name_plural = "Groups"

    def __str__(self):
        return "<{cls} id={id} name={name}, parent={parent}>".format(
            cls=self.__class__.__name__,
            id=self.pk,
            name=self.name,
            parent=self.parent.pk
        )

    @classmethod
    def child_instance_cls_for_parent(cls, parent):
        from greenbudget.app.budget.models import Budget
        from greenbudget.app.template.models import Template
        from greenbudget.app.account.models import BudgetAccount, TemplateAccount  # noqa
        from greenbudget.app.subaccount.models import (
            BudgetSubAccount, TemplateSubAccount)

        mapping = {
            Budget: BudgetAccount,
            Template: TemplateAccount,
            (BudgetAccount, BudgetSubAccount): BudgetSubAccount,
            (TemplateAccount, TemplateSubAccount): TemplateSubAccount
        }
        for k, v in mapping.items():
            if isinstance(parent, k):
                return v
        raise IntegrityError(
            "Unexpected instance %s - must be a valid parent of Group."
            % parent.__class__.__name__
        )

    @property
    def child_instance_cls(self):
        return self.child_instance_cls_for_parent(self.parent)

    @property
    def children(self):
        return self.child_instance_cls.objects.filter(group=self)

    @property
    def budget(self):
        from greenbudget.app.budget.models import BaseBudget
        parent = self.parent
        while not isinstance(parent, BaseBudget):
            parent = parent.parent
        return parent
