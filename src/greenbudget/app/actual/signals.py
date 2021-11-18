from django import dispatch
from django.db import models

from greenbudget.app import signals

from .models import Actual


@dispatch.receiver(signals.post_delete, sender=Actual)
def actual_deleted(instance, **kwargs):
    if instance.owner is not None:
        Actual.objects.reactualize_owner(instance, deleting=True)


@dispatch.receiver(signals.pre_save, sender=Actual)
def actual_to_save(instance, **kwargs):
    instance.validate_before_save()


@dispatch.receiver(models.signals.post_save, sender=Actual)
def actual_saved(instance, **kwargs):
    Actual.objects.reactualize_owner(instance)
