import datetime
import functools
import logging

from django import dispatch

from greenbudget.app import signals

from greenbudget.app.account.models import BudgetAccount, TemplateAccount
from greenbudget.app.actual.models import Actual
from greenbudget.app.fringe.models import Fringe
from greenbudget.app.group.models import (
    BudgetAccountGroup, BudgetSubAccountGroup, TemplateAccountGroup,
    TemplateSubAccountGroup)
from greenbudget.app.subaccount.models import (
    BudgetSubAccount, TemplateSubAccount)

from .models import Budget


logger = logging.getLogger('signals')


@signals.bulk_context.queue_in_context()
def mark_budget_updated(instance):
    logger.info(
        "Marking Budget %s Updated at %s"
        % (instance.pk, datetime.datetime.now())
    )
    instance.save(update_fields=['updated_at'])


@signals.bulk_context.queue_in_context()
def estimate_budget(instance):
    # I don't understand why, but using Account.objects.filter, or using
    # instance.accounts.filter() seems to throw errors occasionally.
    model_cls = BudgetAccount if isinstance(instance, Budget) else TemplateAccount  # noqa
    accounts = model_cls.objects.filter(budget=instance).only('estimated')
    instance.estimated = functools.reduce(
        lambda current, acct: current + (acct.estimated or 0), accounts, 0)
    logger.info(
        "Updating %s %s -> Estimated: %s"
        % (type(instance).__name__, instance.pk, instance.estimated)
    )
    instance.save(update_fields=['estimated'], suppress_budget_update=True)


@signals.bulk_context.queue_in_context()
def actualize_budget(instance):
    accounts = BudgetAccount.objects.filter(budget=instance).only('actual')
    instance.actual = functools.reduce(
        lambda current, acct: current + (acct.actual or 0), accounts.all(), 0)
    logger.info(
        "Updating %s %s -> Actual: %s"
        % (type(instance).__name__, instance.pk, instance.actual)
    )
    instance.save(update_fields=['actual'], suppress_budget_update=True)


def calculate_budget(instance):
    estimate_budget(instance)
    if isinstance(instance, Budget):
        actualize_budget(instance)


@dispatch.receiver(signals.post_save, sender=BudgetAccount)
@dispatch.receiver(signals.post_save, sender=BudgetSubAccount)
@dispatch.receiver(signals.post_save, sender=TemplateAccount)
@dispatch.receiver(signals.post_save, sender=TemplateSubAccount)
@dispatch.receiver(signals.post_save, sender=Fringe)
@dispatch.receiver(signals.post_save, sender=Actual)
@dispatch.receiver(signals.post_save, sender=BudgetAccountGroup)
@dispatch.receiver(signals.post_save, sender=BudgetSubAccountGroup)
@dispatch.receiver(signals.post_save, sender=TemplateAccountGroup)
@dispatch.receiver(signals.post_save, sender=TemplateSubAccountGroup)
@signals.suppress_signal('suppress_budget_update')
def update_budget_updated_at(instance, **kwargs):
    mark_budget_updated(instance.budget)
    instance.clear_flag('suppress_budget_update')
