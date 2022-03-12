from django import dispatch
from django.core.exceptions import ObjectDoesNotExist

from greenbudget.app import signals

from greenbudget.app.account.models import BudgetAccount, TemplateAccount
from greenbudget.app.actual.models import Actual
from greenbudget.app.fringe.models import Fringe
from greenbudget.app.group.models import Group
from greenbudget.app.markup.models import Markup
from greenbudget.app.subaccount.models import (
    BudgetSubAccount, TemplateSubAccount)
from greenbudget.app.template.models import Template

from .cache import budget_instance_cache
from .models import Budget


@dispatch.receiver(signals.post_save, sender=Budget)
@dispatch.receiver(signals.post_save, sender=Template)
def budget_saved(instance, **kwargs):
    budget_instance_cache.invalidate(instance)


@dispatch.receiver(signals.post_save, sender=BudgetAccount)
@dispatch.receiver(signals.post_save, sender=BudgetSubAccount)
@dispatch.receiver(signals.post_save, sender=TemplateAccount)
@dispatch.receiver(signals.post_save, sender=TemplateSubAccount)
@dispatch.receiver(signals.post_save, sender=Fringe)
@dispatch.receiver(signals.post_save, sender=Actual)
@dispatch.receiver(signals.post_save, sender=Group)
@dispatch.receiver(signals.post_save, sender=Markup)
def update_budget_updated_at(instance, **kwargs):
    try:
        budget = instance.budget
    except ObjectDoesNotExist:
        pass
    else:
        budget.mark_updated()


@dispatch.receiver(signals.pre_delete, sender=Budget)
@dispatch.receiver(signals.pre_delete, sender=Template)
def budget_to_be_deleted(instance, **kwargs):
    instance.image.delete(False)
    budget_instance_cache.invalidate(instance)
