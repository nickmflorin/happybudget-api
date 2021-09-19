from django import dispatch

from greenbudget.app import signals
from greenbudget.app.subaccount.models import BudgetSubAccount
from greenbudget.app.subaccount.signals import actualize_subaccount

from .models import Actual


@dispatch.receiver(signals.post_create, sender=Actual)
def actual_created(instance, **kwargs):
    if instance.subaccount is not None:
        actualize_subaccount(instance.subaccount)


@dispatch.receiver(signals.pre_delete, sender=Actual)
def actual_deleted(instance, **kwargs):
    # Note that we have to use the pre_delete signal because we still need to
    # determine which SubAccount(s) have to be reactualized.  We also have to
    # explicitly define the Actuals(s) for the reactualization, so it knows to
    # exclude the Actual that is about to be deleted.
    if instance.subaccount is not None:
        actualize_subaccount(
            instance.subaccount,
            actuals_to_be_deleted=[instance.pk]
        )


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
