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
        suppress_budget_update=True,
        suppress_dispatch_fields=True,
        suppress_history=True
    )


@signals.bulk_context.handler(
    id=lambda instance: instance.pk,
    queue_in_context=True,
    side_effect=lambda instance: signals.SideEffect(
        func=actualize_budget,
        args=(instance.parent, ),
    )
)
def actualize_account(instance, children_to_be_deleted=None,
        markups_to_be_deleted=None):
    instance.actualize(
        children_to_be_deleted=children_to_be_deleted,
        markups_to_be_deleted=markups_to_be_deleted
    )
    if instance.actual != instance.previous_value('actual'):
        instance.save(
            update_fields=["actual"],
            suppress_budget_update=True,
            suppress_history=True,
            suppress_dispatch_fields=True,
        )


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
                'markups_to_be_deleted': markups_to_be_deleted,
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
    # The Account instance can be deleted in the process of deleting it's
    # parent, at which point the parent will be None until that Account
    # instance is deleted.
    if instance.parent is not None:
        calculate_budget(instance.parent, children_to_be_deleted=[instance.pk])
