from django import dispatch

from greenbudget.app import signals
from .models import BudgetAccount, TemplateAccount


@dispatch.receiver(signals.post_save, sender=BudgetAccount)
@dispatch.receiver(signals.post_save, sender=TemplateAccount)
def account_saved(instance, **kwargs):
    instance.invalidate_caches(entities=["detail"])
    instance.parent.invalidate_caches(entities=["children"])
    with signals.post_save.disable(sender=type(instance)):
        instance.calculate(commit=True, trickle=True)


@dispatch.receiver(signals.post_delete, sender=BudgetAccount)
@dispatch.receiver(signals.post_delete, sender=TemplateAccount)
def account_deleted(instance, **kwargs):
    instance.invalidate_caches(entities=["detail"])
    if instance.intermittent_parent is not None:
        instance.intermittent_parent.invalidate_caches(entities=["children"])
        instance.intermittent_parent.calculate(commit=True)


@dispatch.receiver(signals.pre_save, sender=BudgetAccount)
@dispatch.receiver(signals.pre_save, sender=TemplateAccount)
def account_to_save(instance, **kwargs):
    instance.validate_before_save()
