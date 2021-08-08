import functools
import logging

from django import dispatch
from django.contrib.contenttypes.models import ContentType

from greenbudget.app import signals
from greenbudget.app.budget.models import BaseBudget
from greenbudget.app.budget.signals import (
    estimate_budget, actualize_budget, calculate_budget)
from greenbudget.app.group.models import Group
from greenbudget.app.subaccount.models import (
    BudgetSubAccount, TemplateSubAccount)

from .models import BudgetAccount, TemplateAccount


logger = logging.getLogger('signals')


@signals.bulk_context.handler(
    id=lambda instance: instance.pk,
    queue_in_context=True,
    side_effect=lambda instance: signals.SideEffect(
        func=estimate_budget,
        args=(instance.budget, )
    )
)
def estimate_account(instance):
    # NOTE: We cannot use instance.subaccounts.all() due to race conditions on
    # delete events.
    model_cls = BudgetSubAccount
    if isinstance(instance, TemplateAccount):
        model_cls = TemplateSubAccount

    subaccounts = model_cls.objects.filter(
        content_type=ContentType.objects.get_for_model(type(instance)),
        object_id=instance.pk
    ).only('estimated')

    instance.estimated = functools.reduce(
        lambda current, sub: current + (sub.estimated or 0), subaccounts, 0)

    instance.save(update_fields=['estimated'], suppress_budget_update=True)


@signals.bulk_context.handler(
    id=lambda instance: instance.pk,
    queue_in_context=True,
    side_effect=lambda instance: signals.SideEffect(
        func=actualize_budget,
        args=(instance.budget, )
    )
)
def actualize_account(instance):
    subaccounts = BudgetSubAccount.objects.filter(
        content_type=ContentType.objects.get_for_model(BudgetAccount),
        object_id=instance.pk
    ).only('actual')
    instance.actual = functools.reduce(
        lambda current, sub: current + (sub.actual or 0), subaccounts, 0)
    instance.save(update_fields=['actual'], suppress_budget_update=True)


@signals.bulk_context.handler(
    id=lambda instance: instance.pk,
    queue_in_context=True,
    side_effect=lambda instance: [
        signals.SideEffect(
            func=estimate_account,
            args=(instance, )
        ),
        signals.SideEffect(
            func=actualize_account,
            args=(instance, ),
            conditional=isinstance(instance, BudgetAccount)
        )
    ]
)
def calculate_account(instance):
    pass


@dispatch.receiver(signals.post_create, sender=BudgetAccount)
@dispatch.receiver(signals.post_create, sender=TemplateAccount)
def account_created(**kwargs):
    calculate_budget(kwargs['instance'].budget, )


@dispatch.receiver(signals.post_delete, sender=BudgetAccount)
@dispatch.receiver(signals.post_delete, sender=TemplateAccount)
def account_deleted(**kwargs):
    try:
        calculate_budget(kwargs['instance'].budget, )
    except BaseBudget.DoesNotExist:
        # When deleting a Budget, it will also delete the Account(s) associated
        # with it - so the Budget might not exist after a Account is deleted.
        logger.info(
            "Not recalculating budget on account %s deletion because account "
            "was deleted with the budget." % kwargs['intance'].pk
        )


@signals.field_changed_receiver('group', sender=BudgetAccount)
@signals.field_changed_receiver('group', sender=TemplateAccount)
def delete_empty_group(instance, **kwargs):
    # TODO: Eventually, we will want to do this in the background.
    if kwargs['change'].value is None:
        if instance.__class__.objects.filter(
                group_id=kwargs['change'].previous_value).count() == 0:
            logger.info(
                "Deleting group %s after it was removed from %s (id = %s) "
                "because the group no longer has any children."
                % (
                    kwargs['change'].previous_value,
                    instance.__class__.__name__,
                    instance.pk
                )
            )
            # We have to be concerned with race conditions here.
            try:
                group = Group.objects.get(pk=kwargs['change'].previous_value)
            except Group.DoesNotExist:
                pass
            else:
                group.delete()
