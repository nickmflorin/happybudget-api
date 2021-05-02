from colorful.fields import RGBColorField
from polymorphic.models import PolymorphicModel

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from .managers import (
    BudgetAccountGroupManager,
    BudgetSubAccountGroupManager,
    TemplateAccountGroupManager,
    TemplateSubAccountGroupManager
)


class Group(PolymorphicModel):
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        to='user.User',
        related_name='created_groups',
        on_delete=models.SET_NULL,
        null=True
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        to='user.User',
        related_name='updated_groups',
        on_delete=models.SET_NULL,
        null=True
    )
    color_new = models.ForeignKey(
        to='tagging.Color',
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to=models.Q(
            content_types__model='group',
            content_types__app_label='group'
        )
    )
    color = RGBColorField(colors=[
        "#797695",
        "#ff7165",
        "#80cbc4",
        "#ce93d8",
        "#fed835",
        "#c87987",
        "#69f0ae",
        "#a1887f",
        "#81d4fa",
        "#f75776",
        "#66bb6a",
        "#58add6"
    ], default='#EFEFEF')

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

    @property
    def estimated(self):
        estimated = []
        for child in self.children.all():
            if child.estimated is not None:
                estimated.append(child.estimated)
        if len(estimated) != 0:
            return sum(estimated)
        return None


class BudgetAccountGroup(Group):
    name = models.CharField(max_length=128)
    parent = models.ForeignKey(
        to='budget.Budget',
        on_delete=models.CASCADE,
        related_name='groups'
    )
    objects = BudgetAccountGroupManager()
    MAP_FIELDS_FROM_TEMPLATE = ("name", "color")
    MAP_FIELDS_FROM_ORIGINAL = ("name", "color")

    class Meta(Group.Meta):
        verbose_name = "Budget Account Group"
        verbose_name_plural = "Budget Account Groups"
        unique_together = (('parent', 'name'))

    @property
    def variance(self):
        if self.actual is not None and self.estimated is not None:
            return float(self.estimated) - float(self.actual)
        return None

    @property
    def actual(self):
        actuals = []
        for child in self.children.all():
            if child.actual is not None:
                actuals.append(child.actual)
        if len(actuals) != 0:
            return sum(actuals)
        return None


class TemplateAccountGroup(Group):
    name = models.CharField(max_length=128)
    parent = models.ForeignKey(
        to='template.Template',
        on_delete=models.CASCADE,
        related_name='groups'
    )
    objects = TemplateAccountGroupManager()
    MAP_FIELDS_FROM_ORIGINAL = ("name", "color")

    class Meta(Group.Meta):
        verbose_name = "Template Account Group"
        verbose_name_plural = "Template Account Groups"
        unique_together = (('parent', 'name'))


class BudgetSubAccountGroup(Group):
    name = models.CharField(max_length=128)
    content_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.CASCADE,
        limit_choices_to=models.Q(
            app_label='subaccount', model='budgetsubaccount')
        | models.Q(app_label='account', model='budgetaccount')
    )
    object_id = models.PositiveIntegerField(db_index=True)
    parent = GenericForeignKey('content_type', 'object_id')
    objects = BudgetSubAccountGroupManager()
    MAP_FIELDS_FROM_TEMPLATE = ("name", "color")
    MAP_FIELDS_FROM_ORIGINAL = ("name", "color")

    class Meta(Group.Meta):
        verbose_name = "Budget Sub Account Group"
        verbose_name_plural = "Budget Sub Account Groups"
        unique_together = (('object_id', 'content_type', 'name'))

    @property
    def variance(self):
        if self.actual is not None and self.estimated is not None:
            return float(self.estimated) - float(self.actual)
        return None

    @property
    def actual(self):
        actuals = []
        for child in self.children.all():
            if child.actual is not None:
                actuals.append(child.actual)
        if len(actuals) != 0:
            return sum(actuals)
        return None


class TemplateSubAccountGroup(Group):
    name = models.CharField(max_length=128)
    content_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.CASCADE,
        limit_choices_to=models.Q(
            app_label='subaccount', model='templatesubaccount')
        | models.Q(app_label='account', model='templateaccount')
    )
    object_id = models.PositiveIntegerField(db_index=True)
    parent = GenericForeignKey('content_type', 'object_id')
    objects = TemplateSubAccountGroupManager()
    MAP_FIELDS_FROM_ORIGINAL = ("name", "color")

    class Meta(Group.Meta):
        verbose_name = "Template Sub Account Group"
        verbose_name_plural = "Template Sub Account Groups"
        unique_together = (('object_id', 'content_type', 'name'))
