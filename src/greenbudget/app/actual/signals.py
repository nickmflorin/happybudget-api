from django import dispatch
from django.db import models

from greenbudget.app import signals
from greenbudget.app.subaccount.models import BudgetSubAccount
from greenbudget.app.subaccount.signals import actualize_subaccount

from .models import Actual


@dispatch.receiver(signals.post_create, sender=Actual)
@dispatch.receiver(models.signals.post_delete, sender=Actual)
def actual_created_or_deleted(**kwargs):
    try:
        subaccount = kwargs['instance'].subaccount
    except BudgetSubAccount.DoesNotExist:
        # This can happen when this delete is triggered from the deletion of
        # a BudgetSubAccount - the BudgetSubAccount will be deleted, and the
        # on_delete=models.CASCADE will trigger a delete of the Actual - but
        # the BudgetSubAccount associated with the Actual is already gone.
        pass
    else:
        if subaccount is not None:
            actualize_subaccount(subaccount)


@signals.any_fields_changed_receiver(
    fields=['value', 'subaccount'],
    sender=Actual
)
def actual_metrics_changed(**kwargs):
    subaccounts_to_reactualize = []
    for change in kwargs['changes']:
        if change.field == 'subaccount':
            # The previous value of a FK will be the ID, not the full object -
            # for reasons explained in greenbudget.signals.models.
            if change.previous_value is not None:
                old_subaccount = BudgetSubAccount.objects.get(
                    pk=change.previous_value)
                if old_subaccount not in subaccounts_to_reactualize:
                    subaccounts_to_reactualize.append(old_subaccount)
            if change.value is not None \
                    and change.value not in subaccounts_to_reactualize:
                subaccounts_to_reactualize.append(change.value)
        elif change.field == 'value':
            if kwargs['instance'].subaccount is not None \
                    and kwargs['instance'].subaccount not in subaccounts_to_reactualize:  # noqa
                subaccounts_to_reactualize.append(kwargs['instance'].subaccount)

    for subaccount in subaccounts_to_reactualize:
        actualize_subaccount(subaccount)
