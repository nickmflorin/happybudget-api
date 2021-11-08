import logging

from django import dispatch

from greenbudget.app import signals
from greenbudget.app.account.models import BudgetAccount, TemplateAccount
from greenbudget.app.subaccount.models import (
    BudgetSubAccount, TemplateSubAccount)

from .models import Group


logger = logging.getLogger('signals')


@dispatch.receiver(signals.post_save, sender=Group)
def group_saved(instance, **kwargs):
    instance.parent.invalidate_groups_cache()


@dispatch.receiver(signals.pre_delete, sender=Group)
def group_to_be_deleted(instance, **kwargs):
    if instance.intermittent_parent is not None:
        instance.intermittent_parent.invalidate_groups_cache()


@signals.field_changed_receiver('group', sender=BudgetAccount)
@signals.field_changed_receiver('group', sender=TemplateAccount)
@signals.field_changed_receiver('group', sender=BudgetSubAccount)
@signals.field_changed_receiver('group', sender=TemplateSubAccount)
def delete_empty_group(instance, change, **kwargs):
    # Check if the object had been previously assigned a Group that is now
    # empty after the object is moved out of the Group.
    if change.previous_value is not None:
        type(instance).objects.bulk_delete_empty_groups([change.previous_value])
