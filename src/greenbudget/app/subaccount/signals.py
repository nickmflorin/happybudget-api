from django import dispatch
from django.db import IntegrityError

from greenbudget.lib.django_utils.models import generic_fk_instance_change

from greenbudget.app import signals
from greenbudget.app.account.models import Account
from greenbudget.app.budget.cache import budget_actuals_owners_cache
from greenbudget.app.fringe.models import Fringe

from .cache import (
    subaccount_instance_cache,
    subaccount_units_cache,
    invalidate_parent_groups_cache
)
from .models import (
    SubAccount, BudgetSubAccount, TemplateSubAccount, SubAccountUnit)


@dispatch.receiver(signals.m2m_changed, sender=SubAccount.fringes.through)
def validate_fringes(instance, reverse, **kwargs):
    if kwargs['action'] == 'pre_add':
        if reverse:
            subaccounts = SubAccount.objects.filter(pk__in=kwargs['pk_set'])
            for subaccount in subaccounts:
                if subaccount.budget != instance.budget:
                    raise IntegrityError(
                        "The fringes that belong to a sub-account must belong "
                        "to the same budget as that sub-account."
                    )
        else:
            fringes = (Fringe.objects
                .filter(pk__in=kwargs['pk_set'])
                .prefetch_related('budget')
                .only('budget')
                .all())
            for fringe in fringes:
                if fringe.budget != instance.budget:
                    raise IntegrityError(
                        "The fringes that belong to a sub-account must belong "
                        "to the same budget as that sub-account."
                    )


@dispatch.receiver(
    signal=signals.m2m_changed,
    sender=BudgetSubAccount.fringes.through
)
@dispatch.receiver(
    signal=signals.m2m_changed,
    sender=TemplateSubAccount.fringes.through
)
def fringes_changed(instance, action, reverse, model, pk_set, **kwargs):
    if action in ('post_add', 'post_remove'):
        instances = [instance]
        if reverse:
            instances = kwargs['model'].objects.filter(pk__in=kwargs['pk_set'])
        subaccount_instance_cache.invalidate(instances)
        SubAccount.objects.bulk_estimate(instances)


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

        subaccount_instance_cache.invalidate(instances)
        budget_actuals_owners_cache.invalidate([
            b for b in set([instance.budget for instance in instances])
            if b.domain == 'budget'
        ])


@dispatch.receiver(signals.post_save, sender=BudgetSubAccount)
@dispatch.receiver(signals.post_save, sender=TemplateSubAccount)
def subaccount_saved(instance, **kwargs):
    old_parent, new_parent = generic_fk_instance_change(instance)

    instances_to_reestimate = []
    instances_to_recalculate = []

    action = {
        True: instance.actions.CREATE,
        False: instance.actions.UPDATE
    }[kwargs['created']]

    if instance.will_change_parent_estimation(action):
        instances_to_reestimate.append(instance)

    if old_parent != new_parent:
        assert isinstance(old_parent, (SubAccount, Account))
        assert isinstance(new_parent, (SubAccount, Account))

        instances_to_recalculate.extend([old_parent, new_parent])
        instances_to_reestimate = []

    subaccount_instance_cache.invalidate(instance)
    invalidate_parent_groups_cache(instance.parent)
    if instance.domain == 'budget':
        budget_actuals_owners_cache.invalidate(instance.budget)

    SubAccount.objects.bulk_estimate_all(instances_to_reestimate)
    # Note: Using `type(instance).objects` does not seem to work here, might
    # have to do with Django's Meta Classes.
    if isinstance(instance, BudgetSubAccount):
        BudgetSubAccount.objects.bulk_calculate_all(instances_to_recalculate)
    else:
        TemplateSubAccount.objects.bulk_calculate_all(instances_to_recalculate)


@dispatch.receiver(signals.pre_delete, sender=BudgetSubAccount)
@dispatch.receiver(signals.pre_delete, sender=TemplateSubAccount)
def subaccount_to_delete(instance, **kwargs):
    subaccount_instance_cache.invalidate(instance)
    invalidate_parent_groups_cache(instance.parent)
    if instance.domain == 'budget':
        budget_actuals_owners_cache.invalidate(instance.budget)

    # If the SubAccount is being deleted as a part of a CASCADE delete from any
    # of it's parents, do not recalculate the parent as it will be deleted.
    if not any([a.is_deleting for a in instance.ancestors]):
        instance.parent.calculate(
            commit=True,
            trickle=True,
            children_to_delete=[instance.pk]
        )


@dispatch.receiver(signals.post_delete, sender=SubAccountUnit)
def subaccount_unit_deleted(instance, **kwargs):
    subaccount_units_cache.invalidate()


@dispatch.receiver(signals.post_save, sender=SubAccountUnit)
def subaccount_unit_saved(instance, **kwargs):
    subaccount_units_cache.invalidate()
