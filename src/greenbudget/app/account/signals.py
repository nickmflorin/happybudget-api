import functools
import logging

from django import dispatch
from django.contrib.contenttypes.models import ContentType
from django.db import models

from greenbudget.app import signals
from greenbudget.app.budget.signals import (
    estimate_budget, actualize_budget, calculate_budget)
from greenbudget.app.group.models import Group
from greenbudget.app.subaccount.models import BudgetSubAccount

from .models import BudgetAccount, TemplateAccount


logger = logging.getLogger('signals')


reestimate_account = signals.Signal()
reactualize_account = signals.Signal()
recalculate_account = signals.Signal()


@signals.bulk_context.decorate()
def estimate_account(instance):
    subaccounts = instance.subaccounts.only('estimated').all()
    instance.estimated = functools.reduce(
        lambda current, sub: current + (sub.estimated or 0), subaccounts, 0)
    instance.save(update_fields=['estimated'])
    estimate_budget(instance.budget)


@signals.bulk_context.decorate()
def actualize_account(instance):
    subaccounts = BudgetSubAccount.objects.filter(
        content_type=ContentType.objects.get_for_model(BudgetAccount),
        object_id=instance.pk
    ).only('actual')
    instance.actual = functools.reduce(
        lambda current, sub: current + (sub.actual or 0), subaccounts, 0)
    instance.save(update_fields=['actual'])
    actualize_budget(instance.budget)


def calculate_account(instance):
    estimate_account(instance)
    if isinstance(instance, BudgetAccount):
        actualize_account(instance)


@dispatch.receiver(signals.post_create, sender=BudgetAccount)
@dispatch.receiver(signals.post_create, sender=TemplateAccount)
@dispatch.receiver(models.signals.post_delete, sender=BudgetAccount)
@dispatch.receiver(models.signals.post_delete, sender=TemplateAccount)
def account_created_or_deleted(instance, **kwargs):
    calculate_budget(instance.budget)


@dispatch.receiver(reestimate_account, sender=BudgetAccount)
@dispatch.receiver(reestimate_account, sender=TemplateAccount)
def account_reestimation(instance, **kwargs):
    estimate_account(instance)


@dispatch.receiver(reactualize_account, sender=BudgetAccount)
def account_reactualization(instance, **kwargs):
    actualize_account(instance)


@dispatch.receiver(recalculate_account, sender=BudgetAccount)
@dispatch.receiver(recalculate_account, sender=TemplateAccount)
def account_recalculation(instance, **kwargs):
    calculate_account(instance)


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