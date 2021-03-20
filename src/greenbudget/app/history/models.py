from polymorphic.models import PolymorphicModel
import json

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
        ordering = ('-created_at', )
        verbose_name = "Event"
        verbose_name_plural = "Events"

    @property
    def content_object_type(self):
        from greenbudget.app.actual.models import Actual
        from greenbudget.app.account.models import Account
        if isinstance(self.content_object, Actual):
            return "actual"
        elif isinstance(self.content_object, Account):
            return "account"
        else:
            return "subaccount"


class CreateEvent(Event):
    type = "create"

    class Meta:
        get_latest_by = "created_at"
        ordering = ('-created_at', )
        verbose_name = "Create Event"
        verbose_name_plural = "Create Events"


class FieldAlterationEvent(Event):
    type = "field_alteration"
    serialized_old_value = models.TextField()
    serialized_new_value = models.TextField()
    field = models.CharField(max_length=256)

    objects = FieldAlterationManager()

    class Meta:
        get_latest_by = "created_at"
        ordering = ('-created_at', )
        verbose_name = "Field Alteration Event"
        verbose_name_plural = "Field Alteration Events"

    @property
    def old_value(self):
        return json.loads(self.serialized_old_value)

    @property
    def new_value(self):
        return json.loads(self.serialized_new_value)
