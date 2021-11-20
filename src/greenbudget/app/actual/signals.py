from django import dispatch
from django.db import models

from greenbudget.app import signals
from greenbudget.app.budget.cache import budget_actuals_cache

from .models import Actual


@dispatch.receiver(signals.post_delete, sender=Actual)
def actual_deleted(instance, **kwargs):
    budget_actuals_cache.invalidate(instance.intermittent_budget)
    if instance.owner is not None:
        Actual.objects.reactualize_owner(instance, deleting=True)


@dispatch.receiver(signals.pre_save, sender=Actual)
def actual_to_save(instance, **kwargs):
    instance.validate_before_save()


@dispatch.receiver(models.signals.post_save, sender=Actual)
def actual_saved(instance, **kwargs):
    budget_actuals_cache.invalidate(instance.budget)
    Actual.objects.reactualize_owner(instance)
