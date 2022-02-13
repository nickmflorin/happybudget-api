from django import dispatch

from greenbudget.app import signals
from greenbudget.app.budget.cache import budget_groups_cache

from .cache import account_instance_cache
from .models import BudgetAccount, TemplateAccount


@dispatch.receiver(signals.post_save, sender=BudgetAccount)
@dispatch.receiver(signals.post_save, sender=TemplateAccount)
def account_saved(instance, **kwargs):
    account_instance_cache.invalidate(instance)
    budget_groups_cache.invalidate(instance.parent)
    with signals.post_save.disable(sender=type(instance)):
        instance.calculate(commit=True, trickle=True)


@dispatch.receiver(signals.pre_delete, sender=BudgetAccount)
@dispatch.receiver(signals.pre_delete, sender=TemplateAccount)
def account_to_delete(instance, **kwargs):
    account_instance_cache.invalidate(instance)
    budget_groups_cache.invalidate(instance.parent)
    instance.parent.calculate(commit=True, children_to_delete=[instance.pk])
