from django import dispatch
from django.db import models, IntegrityError

from greenbudget.app import signals
from greenbudget.app.subaccount.models import SubAccount
from greenbudget.app.subaccount.signals import estimate_subaccount

from .models import Fringe


@signals.any_fields_changed_receiver(fields=['cutoff', 'rate'], sender=Fringe)
def fringe_metrics_changed(instance, **kwargs):
    subaccounts = SubAccount.objects.filter(fringes=instance)
    with signals.bulk_context:
        for subaccount in subaccounts:
            estimate_subaccount(subaccount)


@dispatch.receiver(models.signals.m2m_changed, sender=SubAccount.fringes.through)
def validate_fringes(sender, **kwargs):
    if kwargs['action'] == 'pre_add' and kwargs['model'] == Fringe:
        fringes = (Fringe.objects
            .filter(pk__in=kwargs['pk_set'])
            .prefetch_related('budget')
            .only('budget')
            .all())
        for fringe in fringes:
            if fringe.budget != kwargs['instance'].budget:
                raise IntegrityError(
                    "The fringes that belong to a sub-account must belong "
                    "to the same budget as that sub-account."
                )
