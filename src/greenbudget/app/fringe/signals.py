from django import dispatch

from greenbudget.app import signals
from greenbudget.app.budget.cache import budget_fringes_cache

from .models import Fringe


@dispatch.receiver(signals.pre_save, sender=Fringe)
def fringe_to_save(instance, **kwargs):
    instance.validate_before_save()


@dispatch.receiver(signals.post_save, sender=Fringe)
def fringe_saved(instance, **kwargs):
    budget_fringes_cache.invalidate(instance.budget)
    if instance.fields_have_changed('unit', 'cutoff', 'rate'):
        Fringe.objects.bulk_estimate_fringe_subaccounts(instance)


@dispatch.receiver(signals.pre_delete, sender=Fringe)
def fringe_to_be_deleted(instance, **kwargs):
    budget_fringes_cache.invalidate(instance.budget)
    Fringe.objects.bulk_estimate_fringe_subaccounts(
        instance,
        fringes_to_be_deleted=[instance.pk]
    )
