import logging

from django import dispatch
from django.db import IntegrityError

from greenbudget.app import signals
from greenbudget.app.account.models import BudgetAccount, TemplateAccount
from greenbudget.app.markup.models import Markup
from greenbudget.app.subaccount.models import (
    BudgetSubAccount, TemplateSubAccount)

from .models import Group


logger = logging.getLogger('signals')


@dispatch.receiver(signals.pre_save, sender=BudgetAccount)
@dispatch.receiver(signals.pre_save, sender=TemplateAccount)
@dispatch.receiver(signals.pre_save, sender=BudgetSubAccount)
@dispatch.receiver(signals.pre_save, sender=TemplateSubAccount)
@dispatch.receiver(signals.pre_save, sender=Markup)
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
@signals.field_changed_receiver('group', sender=Markup)
def delete_empty_group(instance, **kwargs):
    # Check if the object had been previously assigned a Group that is now
    # empty after the object is moved out of the Group.
    if kwargs['change'].previous_value is not None:
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
