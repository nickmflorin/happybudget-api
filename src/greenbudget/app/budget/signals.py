import functools
import threading

from django import dispatch
from django.db.models.signals import post_save

from greenbudget.app import signals

from greenbudget.app.account.models import BudgetAccount, TemplateAccount
from greenbudget.app.actual.models import Actual
from greenbudget.app.fringe.models import Fringe
from greenbudget.app.group.models import (
    BudgetAccountGroup, BudgetSubAccountGroup, TemplateAccountGroup,
    TemplateSubAccountGroup)
from greenbudget.app.subaccount.models import (
    BudgetSubAccount, TemplateSubAccount)
from greenbudget.app.template.models import Template

from .models import Budget


disabled = threading.local()


reestimate_budget = signals.Signal()
reactualize_budget = signals.Signal()
recalculate_budget = signals.Signal()


@signals.bulk_context.decorate()
def estimate_budget(instance):
    # I don't understand why, but using Account.objects.filter, or using
    # instance.accounts.filter() seems to throw errors occasionally.
    model_cls = BudgetAccount if isinstance(instance, Budget) else TemplateAccount  # noqa
    accounts = model_cls.objects.filter(budget=instance).only('estimated')
    instance.estimated = functools.reduce(
        lambda current, acct: current + (acct.estimated or 0), accounts, 0)
    instance.save(update_fields=['estimated'])


@signals.bulk_context.decorate()
def actualize_budget(instance):
    accounts = BudgetAccount.objects.filter(budget=instance).only('actual')
    instance.actual = functools.reduce(
        lambda current, acct: current + (acct.actual or 0), accounts.all(), 0)
    instance.save(update_fields=['actual'])


def calculate_budget(instance):
    estimate_budget(instance)
    if isinstance(instance, Budget):
        actualize_budget(instance)


@ dispatch.receiver(reestimate_budget, sender=Budget)
@ dispatch.receiver(reestimate_budget, sender=Template)
def budget_reestimation(instance, **kwargs):
    estimate_budget(instance)


@ dispatch.receiver(reactualize_budget, sender=Budget)
def budget_reactualization(instance, **kwargs):
    actualize_budget(instance)


@ dispatch.receiver(reestimate_budget, sender=Budget)
@ dispatch.receiver(reestimate_budget, sender=Template)
def budget_recalculation(instance, **kwargs):
    calculate_budget(instance)


@ dispatch.receiver(post_save, sender=BudgetAccount)
@ dispatch.receiver(post_save, sender=BudgetSubAccount)
@ dispatch.receiver(post_save, sender=TemplateAccount)
@ dispatch.receiver(post_save, sender=TemplateSubAccount)
@ dispatch.receiver(post_save, sender=Fringe)
@ dispatch.receiver(post_save, sender=Actual)
@ dispatch.receiver(post_save, sender=BudgetAccountGroup)
@ dispatch.receiver(post_save, sender=BudgetSubAccountGroup)
@ dispatch.receiver(post_save, sender=TemplateAccountGroup)
@ dispatch.receiver(post_save, sender=TemplateSubAccountGroup)
@ signals.bulk_context.decorate(
    recall_id=lambda instance, **kwargs: instance.budget)
@ signals.suppress_signal('suppress_budget_update')
def update_budget_updated_at(instance, **kwargs):
    instance.budget.save(update_fields=['updated_at'])
