from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from happybudget.app import model
from happybudget.app.budgeting.models import BudgetingRowModel

from .managers import GroupManager, BudgetGroupManager, TemplateGroupManager


@model.model(type='group')
class Group(BudgetingRowModel):
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
    content_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.CASCADE,
        limit_choices_to=models.Q(app_label='subaccount', model='subaccount')
        | models.Q(app_label='account', model='account')
        | models.Q(app_label='budget', model='basebudget')
    )
    object_id = models.PositiveIntegerField(db_index=True)
    parent = GenericForeignKey('content_type', 'object_id')

    objects = GroupManager()
    table_pivot = ('object_id', 'content_type_id')
    user_ownership_field = 'parent__user_owner'
    domain_field = 'parent__domain'

    class Meta:
        get_latest_by = "created_at"
        ordering = ('created_at', )
        verbose_name = "Group"
        verbose_name_plural = "Groups"

    def __str__(self):
        return str(self.name)

    @classmethod
    def parse_related_model_table_key_data(cls, parent):
        return {
            'content_type_id': ContentType.objects.get_for_model(parent).pk,
            'object_id': parent.pk
        }

    @property
    def child_instance_cls(self):
        return self.parent.child_instance_cls

    @property
    def children(self):
        return self.child_instance_cls.objects.filter(group=self)

    @property
    def is_empty(self):
        return self.children.count() == 0

    @property
    def budget(self):
        # pylint: disable=import-outside-toplevel
        from happybudget.app.budget.models import BaseBudget
        parent = self.parent
        while not isinstance(parent, BaseBudget):
            parent = parent.parent
        return parent


class BudgetGroup(Group):
    objects = BudgetGroupManager()

    class Meta:
        proxy = True
        verbose_name = "Group"
        verbose_name_plural = "Groups"


class TemplateGroup(Group):
    objects = TemplateGroupManager()

    class Meta:
        proxy = True
        verbose_name = "Group"
        verbose_name_plural = "Groups"
