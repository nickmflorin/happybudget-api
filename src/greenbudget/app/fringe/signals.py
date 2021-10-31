from django import dispatch
from django.db import IntegrityError

from greenbudget.app import signals
from greenbudget.app.budget.cache import budget_fringes_cache
from greenbudget.app.subaccount.models import (
    SubAccount, BudgetSubAccount, TemplateSubAccount)

from .models import Fringe


@dispatch.receiver(signals.post_save, sender=Fringe)
def fringe_saved(instance, **kwargs):
    budget_fringes_cache.invalidate(instance.budget)

    # Since the response for the SubAccount(s) list endpoint only references
    # Fringes by ID, we only have to invalidate that cache when the Fringes
    # are deleted or created.
    if instance.was_just_added():
        for obj in instance.subaccounts.all():
            obj.parent.invalidate_caches(entities=["children"])

    if instance.fields_have_changed('unit', 'cutoff', 'rate'):
        subaccounts = SubAccount.objects.filter(fringes=instance)
        SubAccount.objects.bulk_estimate(subaccounts)


@dispatch.receiver(signals.pre_delete, sender=Fringe)
def fringe_to_be_deleted(instance, **kwargs):
    budget_fringes_cache.invalidate(instance.budget)

    # Since the response for the SubAccount(s) list endpoint only references
    # Fringes by ID, we only have to invalidate that cache when the Fringes
    # are deleted or created.
    for obj in instance.subaccounts.all():
        obj.parent.invalidate_caches(entities=["fringe"])

    subaccounts = SubAccount.objects.filter(fringes=instance)
    SubAccount.objects.bulk_estimate(
        instances=subaccounts,
        fringes_to_be_deleted=[instance.pk]
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
        subaccounts = [instance]
        if reverse:
            subaccounts = model.objects.filter(pk__in=pk_set)
        SubAccount.objects.bulk_estimate(subaccounts)


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
