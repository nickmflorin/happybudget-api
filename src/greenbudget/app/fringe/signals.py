from django import dispatch
from django.db import IntegrityError

from greenbudget.app import signals
from greenbudget.app.subaccount.models import (
    SubAccount, BudgetSubAccount, TemplateSubAccount)
from greenbudget.app.subaccount.signals import estimate_subaccount

from .models import Fringe


@signals.any_fields_changed_receiver(
    fields=['unit', 'cutoff', 'rate'],
    sender=Fringe
)
def fringe_metrics_changed(instance, **kwargs):
    subaccounts = SubAccount.objects.filter(fringes=instance)
    with signals.bulk_context:
        for subaccount in subaccounts:
            estimate_subaccount(subaccount)


@dispatch.receiver(signals.pre_delete, sender=Fringe)
def fringe_deleted(instance, **kwargs):
    # Note that we have to use the pre_delete signal because we still need to
    # determine which SubAccount(s) have to be reestimated.  We also have to
    # explicitly define the Fringe(s) for the reestimation, so it knows to
    # exclude the Fringe that is about to be deleted.
    subaccounts = SubAccount.objects.filter(fringes=instance)
    with signals.bulk_context:
        for subaccount in subaccounts:
            estimate_subaccount(subaccount, fringes_to_be_deleted=[instance.pk])


@dispatch.receiver(
    signal=signals.m2m_changed,
    sender=BudgetSubAccount.fringes.through
)
@dispatch.receiver(
    signal=signals.m2m_changed,
    sender=TemplateSubAccount.fringes.through
)
def fringes_changed(instance, action, reverse, **kwargs):
    if action in ('post_add', 'post_remove'):
        if reverse:
            subaccounts = kwargs['model'].objects.filter(pk__in=kwargs['pk_set'])  # noqa
            with signals.bulk_context:
                for subaccount in subaccounts:
                    estimate_subaccount(subaccount)
        else:
            estimate_subaccount(instance)


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
