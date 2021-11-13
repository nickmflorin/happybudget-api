from greenbudget.app import signals

from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from greenbudget.app.budgeting.utils import get_child_instance_cls

from .managers import GroupManager


@signals.model()
class Group(models.Model):
    type = "group"
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

    class Meta:
        get_latest_by = "created_at"
        ordering = ('created_at', )
        verbose_name = "Group"
        verbose_name_plural = "Groups"

    def __str__(self):
        return "<{cls} id={id} name={name}>".format(
            cls=self.__class__.__name__,
            id=self.pk,
            name=self.name
        )

    @property
    def intermittent_parent(self):
        try:
            return self.parent
        except ObjectDoesNotExist:
            pass

    @classmethod
    def child_instance_cls_for_parent(cls, parent):
        return get_child_instance_cls(parent)

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
