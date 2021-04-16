import datetime
from polymorphic.models import PolymorphicModel
import json

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from greenbudget.lib.utils.dateutils import api_datetime_string

from .managers import EventManager, FieldAlterationManager


class Event(PolymorphicModel):
    type = "event"

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
        limit_choices_to=models.Q(app_label='account', model='budgetaccount')
        | models.Q(app_label='subaccount', model='budgetsubaccount')
    )
    object_id = models.PositiveIntegerField(db_index=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    objects = EventManager()

    non_polymorphic = models.Manager()

    class Meta:
        # See https://code.djangoproject.com/ticket/23076 - this addresses
        # a bug with the Django-polymorphic package in regard to deleting parent
        # models.
        base_manager_name = 'non_polymorphic'
        get_latest_by = "created_at"
        ordering = ('-created_at', )
        verbose_name = "Event"
        verbose_name_plural = "Events"

    @staticmethod
    def serialize_value(value):
        if type(value) is datetime.datetime:
            value = api_datetime_string(value)
        return json.dumps(value)


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
