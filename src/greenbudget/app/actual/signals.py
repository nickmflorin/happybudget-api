from django import dispatch
from django.db import models

from greenbudget.app import signals
from greenbudget.app.budget.cache import budget_actuals_cache

from .models import Actual


@dispatch.receiver(signals.pre_delete, sender=Actual)
def actual_to_delete(instance, **kwargs):
    budget_actuals_cache.invalidate(instance.budget)


# Note: Unfortunately, we have to use a `post_delete` signal here instead of
# combining this logic with the `pre_delete` signal.  The reason is that when
# a Markup is deleted, it's Actual will be deleted as well - so both signals
# will fire before the delete is finished, and the results of the actualization
# will conflict because we would have to explicitly provide both the
# `actuals_to_be_deleted` argument and the `markups_to_be_deleted` argument at
# the same time.
@dispatch.receiver(signals.post_delete, sender=Actual)
def actual_deleted(instance, **kwargs):
    if instance.owner is not None:
        Actual.objects.bulk_actualize_all([instance.owner])


@dispatch.receiver(signals.pre_save, sender=Actual)
def actual_to_save(instance, **kwargs):
    budget_actuals_cache.invalidate(instance.budget)


@dispatch.receiver(models.signals.post_save, sender=Actual)
def actual_saved(instance, **kwargs):
    owners_to_reactualize = Actual.objects.get_owners_to_reactualize(instance)
    Actual.objects.bulk_actualize_all(owners_to_reactualize)
