from django import dispatch

from happybudget.app import signals
from happybudget.app.budget.cache import budget_groups_cache

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
    # If the Account is being deleted as a part of a CASCADE delete from the
    # Budget deleting, do not recalculate the Budget.
    if not instance.parent.is_deleting:
        instance.parent.calculate(commit=True, children_to_delete=[instance.pk])
