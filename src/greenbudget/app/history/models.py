from polymorphic.models import PolymorphicModel

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from .managers import EventManager, FieldAlterationManager


class Event(PolymorphicModel):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        to='user.User',
        related_name='events',
        on_delete=models.CASCADE,
        db_index=True
    )
    content_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.CASCADE,
        limit_choices_to=models.Q(app_label='account', model='account')
        | models.Q(app_label='subaccount', model='subaccount')
        | models.Q(app_label='actual', model='actual')
    )
    object_id = models.PositiveIntegerField(db_index=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    objects = EventManager()

    class Meta:
        get_latest_by = "created_at"
        ordering = ('created_at', )
        verbose_name = "Event"
        verbose_name_plural = "Events"


class FieldAlterationEvent(Event):
    type = "field_alteration"
    old_value = models.TextField(null=True)
    new_value = models.TextField(null=True)
    field = models.CharField(max_length=256)

    objects = FieldAlterationManager()

    class Meta:
        get_latest_by = "created_at"
        ordering = ('created_at', )
        verbose_name = "Field Alteration Event"
        verbose_name_plural = "Field Alteration Events"
