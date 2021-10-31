from django import dispatch
from django.db import IntegrityError, models

from greenbudget.app import signals
from greenbudget.app.budget.cache import budget_actuals_cache

from .models import Actual


@dispatch.receiver(signals.post_delete, sender=Actual)
def actual_deleted(instance, **kwargs):
    budget_actuals_cache.invalidate(instance.budget)
    if instance.owner is not None:
        Actual.objects.reactualize_owner(instance, deleting=True)


@dispatch.receiver(signals.pre_save, sender=Actual)
def validate_actual(instance, **kwargs):
    try:
        budget = instance.budget
    except Actual.budget.RelatedObjectDoesNotExist:
        pass
    else:
        if instance.owner is not None and instance.owner.budget != budget:
            raise IntegrityError(
                "Can only add actuals with the same parent as the instance.")
        elif instance.contact is not None \
                and instance.contact.user != instance.created_by:
            raise IntegrityError(
                "Cannot assign a contact created by one user to an actual "
                "created by another user."
            )


@dispatch.receiver(models.signals.post_save, sender=Actual)
def actual_saved(instance, **kwargs):
    budget_actuals_cache.invalidate(instance.budget)
    Actual.objects.reactualize_owner(instance)
