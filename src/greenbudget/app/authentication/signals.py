from django import dispatch

from greenbudget.app import signals
from greenbudget.app.budget.cache import budget_instance_cache

from .models import ShareToken


@dispatch.receiver(signals.pre_save, sender=ShareToken)
def share_token_to_save(instance, **kwargs):
    # Right now, the ShareToken model is only used for Budget(s).
    budget_instance_cache.invalidate(instance.instance)


@dispatch.receiver(signals.pre_delete, sender=ShareToken)
def share_token_to_delete(instance, **kwargs):
    # Right now, the ShareToken model is only used for Budget(s).
    budget_instance_cache.invalidate(instance.instance)
