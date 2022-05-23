from django import dispatch

from happybudget.app import signals
from happybudget.app.account.models import BudgetAccount, TemplateAccount
from happybudget.app.budgeting.cache import invalidate_groups_cache
from happybudget.app.subaccount.models import (
    BudgetSubAccount, TemplateSubAccount)

from .models import Group


@dispatch.receiver(signals.post_save, sender=Group)
def group_saved(instance, **kwargs):
    invalidate_groups_cache(instance.parent)


@dispatch.receiver(signals.pre_delete, sender=Group)
def group_to_be_deleted(instance, **kwargs):
    invalidate_groups_cache(instance.parent)


@signals.field_changed_receiver('group', sender=BudgetAccount)
@signals.field_changed_receiver('group', sender=TemplateAccount)
@signals.field_changed_receiver('group', sender=BudgetSubAccount)
@signals.field_changed_receiver('group', sender=TemplateSubAccount)
def delete_empty_group(instance, change, **kwargs):
    # Check if the object had been previously assigned a Group that is now
    # empty after the object is moved out of the Group.
    if change.previous_value is not None and not instance.is_deleting:
        type(instance).objects.bulk_delete_empty_groups([change.previous_value])
