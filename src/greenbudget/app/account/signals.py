import logging

from django import dispatch

from greenbudget.app import signals
from greenbudget.app.budget.signals import (
    estimate_budget, actualize_budget, calculate_budget)

from .models import BudgetAccount, TemplateAccount


logger = logging.getLogger('signals')


@signals.bulk_context.handler(
    id=lambda instance: instance.pk,
    queue_in_context=True,
    side_effect=lambda instance: signals.SideEffect(
        func=estimate_budget,
        args=(instance.parent, )
    )
)
def estimate_account(instance, markups_to_be_deleted=None,
        children_to_be_deleted=None):
    instance.estimate(
        markups_to_be_deleted=markups_to_be_deleted,
        children_to_be_deleted=children_to_be_deleted
    )
    instance.save(
        update_fields=list(instance.ESTIMATED_FIELDS),
        suppress_budget_update=True
    )


@signals.bulk_context.handler(
    id=lambda instance: instance.pk,
    queue_in_context=True,
    side_effect=lambda instance: signals.SideEffect(
        func=actualize_budget,
        args=(instance.parent, )
    )
)
def actualize_account(instance, children_to_be_deleted=None):
    instance.actualize(
        children_to_be_deleted=children_to_be_deleted)
    instance.save(update_fields=["actual"], suppress_budget_update=True)


@signals.bulk_context.handler(
    id=lambda instance: instance.pk,
    queue_in_context=True,
    side_effect=lambda instance, markups_to_be_deleted, children_to_be_deleted: [  # noqa
        signals.SideEffect(
            func=estimate_account,
            args=(instance, ),
            kwargs={
                'children_to_be_deleted': children_to_be_deleted,
                'markups_to_be_deleted': markups_to_be_deleted
            }
        ),
        signals.SideEffect(
            func=actualize_account,
            args=(instance, ),
            kwargs={
                'children_to_be_deleted': children_to_be_deleted,
            },
            conditional=isinstance(instance, BudgetAccount)
        )
    ]
)
def calculate_account(instance, markups_to_be_deleted=None,
        children_to_be_deleted=None):
    pass


@dispatch.receiver(signals.post_create, sender=BudgetAccount)
@dispatch.receiver(signals.post_create, sender=TemplateAccount)
def account_created(instance, **kwargs):
    calculate_budget(instance.parent, )


@dispatch.receiver(signals.post_delete, sender=BudgetAccount)
@dispatch.receiver(signals.post_delete, sender=TemplateAccount)
def account_deleted(instance, **kwargs):
    from greenbudget.app.budget.models import BaseBudget
    try:
        calculate_budget(instance.parent)
    except BaseBudget.DoesNotExist:
        # When deleting a Budget, it will also delete the Account(s) associated
        # with it - so the Budget might not exist after a Account is deleted.
        logger.info(
            "Not recalculating budget on account %s deletion because account "
            "was deleted with the budget." % instance.pk
        )
