from django import dispatch

from greenbudget.lib.django_utils.models import generic_fk_instance_change

from greenbudget.app import signals
from greenbudget.app.account.models import Account
from greenbudget.app.budget.cache import budget_actuals_owner_tree_cache

from .cache import subaccount_units_cache
from .models import (
    SubAccount, BudgetSubAccount, TemplateSubAccount, SubAccountUnit)


@dispatch.receiver(
    signal=signals.m2m_changed,
    sender=BudgetSubAccount.fringes.through
)
@dispatch.receiver(
    signal=signals.m2m_changed,
    sender=TemplateSubAccount.fringes.through
)
def invalidate_caches_on_fringe_changes(instance, action, reverse, **kwargs):
    if action in ('post_add', 'post_remove'):
        instances = [instance]
        if reverse:
            instances = kwargs['model'].objects.filter(pk__in=kwargs['pk_set'])
        for instance in instances:
            instance.invalidate_caches(entities=["detail"])


@dispatch.receiver(
    signal=signals.m2m_changed,
    sender=BudgetSubAccount.markups.through
)
@dispatch.receiver(
    signal=signals.m2m_changed,
    sender=TemplateSubAccount.markups.through
)
def invalidate_caches_on_markup_changes(instance, action, reverse, **kwargs):
    if action in ('post_add', 'post_remove'):
        instances = [instance]
        if reverse:
            instances = kwargs['model'].objects.filter(pk__in=kwargs['pk_set'])
        for instance in instances:
            instance.invalidate_caches(entities=["detail"])

        budgets = set([instance.budget for instance in instances])
        budgets = [b for b in budgets if b.domain == 'budget']
        budget_actuals_owner_tree_cache.invalidate(budgets)


@dispatch.receiver(signals.post_save, sender=BudgetSubAccount)
@dispatch.receiver(signals.post_save, sender=TemplateSubAccount)
def subaccount_saved(instance, **kwargs):
    instance.invalidate_caches(["detail"])
    instance.parent.invalidate_caches(["children"])

    CALCULATING_FIELDS = ('rate', 'quantity', 'multiplier')
    old_parent, new_parent = generic_fk_instance_change(instance)

    instances_to_reestimate = []
    instances_to_recalculate = []

    if instance.was_just_added() \
            or instance.fields_have_changed(*CALCULATING_FIELDS):
        instances_to_reestimate.append(instance)

    if old_parent != new_parent:
        assert isinstance(old_parent, (SubAccount, Account))
        assert isinstance(new_parent, (SubAccount, Account))

        # If a SubAccount has children SubAccount(s), the fields used to
        # derive calculated values are no longer used since the calculated
        # values are derived from the children, not the attributes on that
        # SubAccount.
        if isinstance(new_parent, SubAccount):
            new_parent.clear_deriving_fields(commit=False)
        instances_to_recalculate.extend([old_parent, new_parent])
        instances_to_reestimate = []

    if isinstance(instance, BudgetSubAccount):
        BudgetSubAccount.objects.bulk_calculate_all(instances_to_recalculate)
        budget_actuals_owner_tree_cache.invalidate(instance.budget)
    else:
        TemplateSubAccount.objects.bulk_calculate_all(instances_to_recalculate)


@dispatch.receiver(signals.pre_delete, sender=BudgetSubAccount)
def subaccount_to_delete(instance, **kwargs):
    budget_actuals_owner_tree_cache.invalidate(instance.budget)


@dispatch.receiver(signals.post_delete, sender=BudgetSubAccount)
@dispatch.receiver(signals.post_delete, sender=TemplateSubAccount)
def subaccount_deleted(instance, **kwargs):
    instance.invalidate_caches(["detail"])
    if instance.intermittent_parent is not None:
        instance.intermittent_parent.invalidate_caches(["children"])
        instance.intermittent_parent.calculate(commit=True, trickle=True)

        type(instance.intermittent_parent).objects.bulk_calculate(
            [instance.intermittent_parent])


@dispatch.receiver(signals.pre_save, sender=BudgetSubAccount)
@dispatch.receiver(signals.pre_save, sender=TemplateSubAccount)
def subaccount_to_save(instance, **kwargs):
    instance.validate_before_save()


@dispatch.receiver(signals.post_delete, sender=SubAccountUnit)
def subaccount_unit_deleted(instance, **kwargs):
    subaccount_units_cache.invalidate()


@dispatch.receiver(signals.post_save, sender=SubAccountUnit)
def subaccount_unit_saved(instance, **kwargs):
    subaccount_units_cache.invalidate()
