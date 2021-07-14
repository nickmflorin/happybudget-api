import functools
from polymorphic.models import PolymorphicModel

from greenbudget.app import signals

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from .managers import GroupManager


class Group(PolymorphicModel):
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        to='user.User',
        related_name='created_groups',
        on_delete=models.CASCADE,
        editable=False
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        to='user.User',
        related_name='updated_groups',
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

    non_polymorphic = models.Manager()

    class Meta:
        # See https://code.djangoproject.com/ticket/23076 - this addresses
        # a bug with the Django-polymorphic package in regard to deleting parent
        # models.
        base_manager_name = 'non_polymorphic'
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

    @property
    def estimated(self):
        children = self.children.only('estimated')
        return functools.reduce(
            lambda current, c: current + (c.estimated or 0), children, 0)


@signals.model('suppress_budget_update')
class BudgetAccountGroup(Group):
    parent = models.ForeignKey(
        to='budget.Budget',
        on_delete=models.CASCADE,
        related_name='groups'
    )
    objects = GroupManager()
    FIELDS_TO_DUPLICATE = ("name", "color")

    class Meta(Group.Meta):
        verbose_name = "Account Group"
        verbose_name_plural = "Account Groups"

    @property
    def budget(self):
        return self.parent

    @property
    def variance(self):
        return self.estimated - self.actual

    @property
    def actual(self):
        children = self.children.only('actual')
        return functools.reduce(
            lambda current, c: current + (c.actual or 0), children, 0)


@signals.model('suppress_budget_update')
class TemplateAccountGroup(Group):
    parent = models.ForeignKey(
        to='template.Template',
        on_delete=models.CASCADE,
        related_name='groups'
    )
    objects = GroupManager()
    FIELDS_TO_DUPLICATE = ("name", "color")
    FIELDS_TO_DERIVE = ("name", "color")

    @property
    def budget(self):
        return self.parent

    class Meta(Group.Meta):
        verbose_name = "Account Group"
        verbose_name_plural = "Account Groups"


@signals.model('suppress_budget_update')
class BudgetSubAccountGroup(Group):
    content_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.CASCADE,
        limit_choices_to=models.Q(
            app_label='subaccount', model='budgetsubaccount')
        | models.Q(app_label='account', model='budgetaccount')
    )
    object_id = models.PositiveIntegerField(db_index=True)
    parent = GenericForeignKey('content_type', 'object_id')
    objects = GroupManager()

    FIELDS_TO_DUPLICATE = ("name", "color")

    class Meta(Group.Meta):
        verbose_name = "Sub Account Group"
        verbose_name_plural = "Sub Account Groups"

    @property
    def budget(self):
        return self.parent.budget

    @property
    def variance(self):
        return self.estimated - self.actual

    @property
    def actual(self):
        children = self.children.only('actual')
        return functools.reduce(
            lambda current, c: current + (c.actual or 0), children, 0)


@signals.model('suppress_budget_update')
class TemplateSubAccountGroup(Group):
    content_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.CASCADE,
        limit_choices_to=models.Q(
            app_label='subaccount', model='templatesubaccount')
        | models.Q(app_label='account', model='templateaccount')
    )
    object_id = models.PositiveIntegerField(db_index=True)
    parent = GenericForeignKey('content_type', 'object_id')
    objects = GroupManager()

    FIELDS_TO_DERIVE = ("name", "color")
    FIELDS_TO_DUPLICATE = ("name", "color")

    class Meta(Group.Meta):
        verbose_name = "Sub Account Group"
        verbose_name_plural = "Sub Account Groups"

    @property
    def budget(self):
        return self.parent.budget
