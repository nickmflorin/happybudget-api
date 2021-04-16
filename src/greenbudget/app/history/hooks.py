import logging

from django.conf import settings

from greenbudget.app.history.models import (
    Event, FieldAlterationEvent, CreateEvent)

logger = logging.getLogger('greenbudget')


def on_field_change(instance, field, data):
    if getattr(settings, 'TRACK_MODEL_HISTORY', False) is False:
        logger.info(
            "Suppressing model tracking behavior for %s - "
            "`settings.TRACK_MODEL_HISTORY` is either not defined or False."
            % instance.__class__.__name__
        )
        return
    FieldAlterationEvent.objects.create(
        content_object=instance,
        field=field,
        serialized_old_value=Event.serialize_value(data['previous_value']),
        serialized_new_value=Event.serialize_value(data['new_value']),
        user=data['user']
    )


def on_create(instance, data):
    if getattr(settings, 'TRACK_MODEL_HISTORY', False) is False:
        logger.info(
            "Suppressing model tracking behavior for %s - "
            "`settings.TRACK_MODEL_HISTORY` is either not defined or False."
            % instance.__class__.__name__
        )
        return
    CreateEvent.objects.create(
        content_object=instance,
        user=data['user']
    )
