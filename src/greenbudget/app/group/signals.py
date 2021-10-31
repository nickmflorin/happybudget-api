import logging

from django import dispatch
from django.db import IntegrityError

from greenbudget.app import signals
from greenbudget.app.account.cache import account_groups_cache
from greenbudget.app.account.models import (
    Account, BudgetAccount, TemplateAccount)
from greenbudget.app.budget.cache import budget_groups_cache
from greenbudget.app.budget.models import BaseBudget
from greenbudget.app.markup.models import Markup
from greenbudget.app.subaccount.cache import subaccount_groups_cache
from greenbudget.app.subaccount.models import (
    SubAccount, BudgetSubAccount, TemplateSubAccount)

from .models import Group


logger = logging.getLogger('signals')


def invalidate_parent_groups_cache(instances):
    instances = instances if hasattr(instances, '__iter__') else [instances]
    for instance in instances:
        assert isinstance(instance.parent, (Account, SubAccount, BaseBudget))
        if isinstance(instance.parent, Account):
            account_groups_cache.invalidate(instance.parent)
        elif isinstance(instance.parent, SubAccount):
            subaccount_groups_cache.invalidate(instance.parent)
        else:
            budget_groups_cache.invalidate(instance.parent)


@dispatch.receiver(signals.post_save, sender=Group)
def group_saved(instance, **kwargs):
    invalidate_parent_groups_cache(instance)


@dispatch.receiver(signals.pre_delete, sender=Group)
def group_to_be_deleted(instance, **kwargs):
    invalidate_parent_groups_cache(instance)


@dispatch.receiver(signals.pre_save, sender=BudgetAccount)
@dispatch.receiver(signals.pre_save, sender=TemplateAccount)
@dispatch.receiver(signals.pre_save, sender=BudgetSubAccount)
@dispatch.receiver(signals.pre_save, sender=TemplateSubAccount)
def validate_group(instance, **kwargs):
    if instance.group is not None:
        if instance.group.parent != instance.parent:
            raise IntegrityError(
                "Can only add groups with the same parent as the instance."
            )
        if isinstance(instance, Markup) \
                and instance.group in instance.groups.all():
            raise IntegrityError(
                "Cannot add a markup to a group if that group already exists "
                "as a child of that markup."
            )


@signals.field_changed_receiver('group', sender=BudgetAccount)
@signals.field_changed_receiver('group', sender=TemplateAccount)
@signals.field_changed_receiver('group', sender=BudgetSubAccount)
@signals.field_changed_receiver('group', sender=TemplateSubAccount)
def delete_empty_group(instance, change, **kwargs):
    # Check if the object had been previously assigned a Group that is now
    # empty after the object is moved out of the Group.
    if change.previous_value is not None:
        type(instance).objects.bulk_delete_empty_groups([change.previous_value])
