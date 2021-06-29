import logging

from django import dispatch
from django.conf import settings
from django.db import transaction

from greenbudget.app import signals
from greenbudget.app.account.models import BudgetAccount
from greenbudget.app.subaccount.models import BudgetSubAccount

from .models import Event, CreateEvent, FieldAlterationEvent


logger = logging.getLogger('history')


def model_history_enabled(sender):
    # We need the ability to turn off all model history tracking from the
    # Django settings - so only proceed if this setting is explicitly set
    # to True.
    if getattr(settings, 'TRACK_MODEL_HISTORY', False) is False:
        logger.info(
            "Suppressing history tracking behavior for %s because "
            "settings.TRACK_MODEL_HISTORY is either not defined "
            "or False." % sender.__name__
        )
        return False
    return True


def model_supports_history(model):
    # Eventually, we want this to be more flexible - so that it can support
    # any model with the correct flags.  However, the Event model is
    # currently restricted by it's Generic Foreign Key to these types.
    if model not in (BudgetAccount, BudgetSubAccount):
        raise Exception(
            "History tracking currently not supported for model %s."
            % model.__name__
        )


@dispatch.receiver(signals.post_create_by_user)
@signals.suppress_signal(params=[('track_changes', False)])
def track_create_history(instance, **kwargs):
    should_track_history = getattr(
        kwargs['sender'], 'TRACK_MODEL_HISTORY', False)
    should_track_create_history = getattr(
        kwargs['sender'], 'TRACK_MODEL_CREATE_HISTORY', False)

    if (should_track_history or should_track_create_history):
        model_supports_history(kwargs['sender'])
        if not model_history_enabled(kwargs['sender']):
            return

        # TODO: Eventually, we are going to want to do this in the background.
        CreateEvent.objects.create(content_object=instance, user=kwargs['user'])


@dispatch.receiver(signals.fields_changed)
@signals.suppress_signal(params=[('track_changes', False)])
def track_change_history(instance, **kwargs):
    should_track_history = getattr(
        kwargs['sender'], 'TRACK_MODEL_HISTORY', False)
    should_track_change_history = getattr(
        kwargs['sender'], 'TRACK_FIELD_CHANGE_HISTORY', [])

    if (should_track_history or should_track_change_history):
        model_supports_history(kwargs['sender'])
        if not model_history_enabled(kwargs['sender']):
            return

        # TODO: Start doing this in the background.
        with transaction.atomic():
            for change in [c for c in kwargs['changes']
                    if c.field in should_track_change_history]:
                FieldAlterationEvent.objects.create(
                    content_object=instance,
                    field=change.field,
                    serialized_old_value=Event.serialize_value(
                        change.previous_value),
                    serialized_new_value=Event.serialize_value(change.value),
                    user=kwargs['user']
                )
