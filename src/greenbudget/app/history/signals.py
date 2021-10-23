import logging

from django import dispatch
from django.db import transaction

from greenbudget.app import signals

from .models import Event, CreateEvent, FieldAlterationEvent


logger = logging.getLogger('history')


@dispatch.receiver(signals.model_history_created)
def track_create_history(instance, **kwargs):
    # TODO: Eventually, we are going to want to do this in the background.
    CreateEvent.objects.create(content_object=instance, user=kwargs['user'])


@dispatch.receiver(signals.model_history_changed)
def track_change_history(instance, changes, **kwargs):
    # TODO: Eventually, we are going to want to do this in the background.
    with transaction.atomic():
        for change in changes:
            FieldAlterationEvent.objects.create(
                content_object=instance,
                field=change.field,
                serialized_old_value=Event.serialize_value(
                    change.previous_value),
                serialized_new_value=Event.serialize_value(change.value),
                user=kwargs['user']
            )
