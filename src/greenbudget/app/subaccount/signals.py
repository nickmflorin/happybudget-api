import functools
import logging

from django import dispatch
from django.contrib.contenttypes.models import ContentType
from django.db import models

from greenbudget.app import signals
from greenbudget.app.account.signals import (
    estimate_account, actualize_account, calculate_account)
from greenbudget.app.fringe.utils import fringe_value
from greenbudget.app.group.models import Group

from .models import BudgetSubAccount, TemplateSubAccount


logger = logging.getLogger('signals')


@signals.bulk_context.queue_in_context()
def actualize_subaccount(instance):
    # We cannot do .only('actual') here because the subaccounts are polymorphic.
    # We should figure out how to do that.
    subaccounts = BudgetSubAccount.objects.filter(
        content_type=ContentType.objects.get_for_model(BudgetSubAccount),
        object_id=instance.pk
    ).only('actual')
    actuals = instance.actuals.only('value')

    instance.actual = functools.reduce(
        lambda current, sub: current + (sub.actual or 0), subaccounts.all(), 0)
    instance.actual += functools.reduce(
        lambda current, actual: current + (actual.value or 0), actuals.all(), 0)

    instance.save(update_fields=['actual'], suppress_budget_update=True)

    # There are weird cases (like CASCADE deletes) where non-nullable fields
    # will be temporarily null - they just won't be saved in a NULL state.
    if instance.parent is not None:
        if isinstance(instance.parent, (BudgetSubAccount, TemplateSubAccount)):
            actualize_subaccount(instance.parent)
        else:
            actualize_account(instance.parent)


@signals.bulk_context.queue_in_context()
def estimate_subaccount(instance):
    subaccounts = instance.subaccounts.only('estimated')
    if subaccounts.count() == 0:
        if instance.quantity is not None and instance.rate is not None:
            multiplier = instance.multiplier or 1.0
            value = float(instance.quantity) * float(instance.rate) * float(multiplier)  # noqa
            # TODO: Eventually, we want to have the value fringed on post_save
            # signals for the Fringes themselves.
            instance.estimated = fringe_value(value, instance.fringes.all())
        else:
            instance.estimated = 0.0
    else:
        instance.estimated = functools.reduce(
            lambda current, sub: current + (sub.estimated or 0),
            subaccounts.all(),
            0
        )

    instance.save(update_fields=['estimated'], suppress_budget_update=True)

    if isinstance(instance.parent, (BudgetSubAccount, TemplateSubAccount)):
        estimate_subaccount(instance.parent)
    else:
        estimate_account(instance.parent)


def calculate_subaccount(instance):
    estimate_subaccount(instance)
    if isinstance(instance, BudgetSubAccount):
        actualize_subaccount(instance)


def calculate_parent(parent):
    if isinstance(parent, (BudgetSubAccount, TemplateSubAccount)):
        calculate_subaccount(parent)
    else:
        calculate_account(parent)


@signals.any_fields_changed_receiver(
    fields=['rate', 'multiplier', 'quantity'],
    sender=BudgetSubAccount
)
@signals.any_fields_changed_receiver(
    fields=['rate', 'multiplier', 'quantity'],
    sender=TemplateSubAccount
)
def subaccount_reestimation(instance, **kwargs):
    estimate_subaccount(instance)


@dispatch.receiver(signals.post_create, sender=BudgetSubAccount)
@dispatch.receiver(signals.post_create, sender=TemplateSubAccount)
def subaccount_recalculation(instance, **kwargs):
    calculate_subaccount(instance)


@dispatch.receiver(models.signals.post_delete, sender=BudgetSubAccount)
@dispatch.receiver(models.signals.post_delete, sender=TemplateSubAccount)
def subaccount_deleted(instance, **kwargs):
    if instance.parent is not None:
        calculate_parent(instance.parent)


@signals.any_fields_changed_receiver(
    fields=['object_id', 'content_type'],
    sender=BudgetSubAccount
)
@signals.any_fields_changed_receiver(
    fields=['object_id', 'content_type'],
    sender=TemplateSubAccount
)
def subaccount_parent_changed(instance, **kwargs):
    changes = kwargs['changes']

    previous_content_type_id = instance.content_type_id
    new_content_type_id = instance.content_type_id
    if changes.get_change_for_field('content_type') is not None:
        content_type_change = changes.get_change_for_field('content_type')
        previous_content_type_id = content_type_change.previous_value
        new_content_type_id = content_type_change.value.pk

    previous_object_id = instance.object_id
    new_object_id = instance.object_id
    if changes.get_change_for_field('object_id') is not None:
        object_id_change = changes.get_change_for_field('object_id')
        previous_object_id = object_id_change.previous_value
        new_object_id = object_id_change.value

    # NOTE: The object_id and content_type of a SubAccount can never be null.
    previous_model_cls = ContentType.objects.get(
        pk=previous_content_type_id).model_class()
    previous_parent = previous_model_cls.objects.get(pk=previous_object_id)

    new_model_cls = ContentType.objects.get(
        pk=new_content_type_id).model_class()
    new_parent = new_model_cls.objects.get(pk=new_object_id)

    calculate_parent(previous_parent)
    calculate_parent(new_parent)


@signals.field_changed_receiver('group', sender=BudgetSubAccount)
@signals.field_changed_receiver('group', sender=TemplateSubAccount)
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


@dispatch.receiver(signals.post_save, sender=BudgetSubAccount)
@dispatch.receiver(signals.post_save, sender=TemplateSubAccount)
def remove_parent_calculated_fields(instance, **kwargs):
    # If a SubAccount has children SubAccount(s), the fields used to derive
    # calculated values are no longer used since the calculated values are
    # derived from the children, not the attributes on that SubAccount.
    if isinstance(instance.parent, (BudgetSubAccount, TemplateSubAccount)):
        for field in instance.DERIVING_FIELDS:
            setattr(instance.parent, field, None)
        instance.parent.fringes.set([])
        if isinstance(instance.parent, BudgetSubAccount):
            instance.parent.save(
                update_fields=instance.DERIVING_FIELDS,
                track_changes=False,
                suppress_budget_update=True
            )
        else:
            instance.parent.save(
                update_fields=instance.DERIVING_FIELDS,
                suppress_budget_update=True
            )
