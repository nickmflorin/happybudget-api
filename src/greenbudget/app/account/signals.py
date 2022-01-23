from django import dispatch

from greenbudget.app import signals

from .cache import account_instance_cache
from .models import BudgetAccount, TemplateAccount


@dispatch.receiver(signals.post_save, sender=BudgetAccount)
@dispatch.receiver(signals.post_save, sender=TemplateAccount)
def account_saved(instance, **kwargs):
    account_instance_cache.invalidate(instance)
    with signals.post_save.disable(sender=type(instance)):
        instance.calculate(commit=True, trickle=True)


@dispatch.receiver(signals.pre_delete, sender=BudgetAccount)
@dispatch.receiver(signals.pre_delete, sender=TemplateAccount)
def account_to_delete(instance, **kwargs):
    account_instance_cache.invalidate(instance)
    instance.parent.calculate(commit=True, children_to_delete=[instance.pk])


@dispatch.receiver(signals.pre_save, sender=BudgetAccount)
@dispatch.receiver(signals.pre_save, sender=TemplateAccount)
def account_to_save(instance, **kwargs):
    instance.validate_before_save()
