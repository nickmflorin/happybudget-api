import logging

from django import dispatch
from django.db import IntegrityError

from greenbudget.app import signals
from greenbudget.app.signals.utils import generic_foreign_key_instance_change
from greenbudget.app.account.models import BudgetAccount, Account
from greenbudget.app.account.signals import actualize_account, estimate_account
from greenbudget.app.budget.models import Budget
from greenbudget.app.budget.signals import actualize_budget
from greenbudget.app.subaccount.models import BudgetSubAccount, SubAccount
from greenbudget.app.subaccount.signals import (
    actualize_subaccount, estimate_subaccount)

from .models import Markup


logger = logging.getLogger('signals')


@dispatch.receiver(signals.m2m_changed, sender=Account.markups.through)
@dispatch.receiver(signals.m2m_changed, sender=SubAccount.markups.through)
def delete_empty_markups(instance, reverse, **kwargs):
    if kwargs['action'] == 'post_remove':
        # Depending on whether or not the M2M was changed on the forward or
        # reverse side of the field, the instance will refer to different
        # things.
        markups = [instance]
        if not reverse:
            markups = Markup.objects.filter(pk__in=kwargs['pk_set']).all()

        for markup in markups:
            if markup.is_empty:
                logger.info(
                    "Deleting markup %s after it was removed from %s (id = %s) "
                    "because the markup no longer has any children."
                    % (
                        markup.pk,
                        instance.__class__.__name__,
                        instance.pk
                    )
                )
                # We have to be concerned with race conditions here.
                try:
                    markup.delete()
                except Markup.DoesNotExist:
                    pass


def estimate_instance(instance, **kwargs):
    mapping = {
        Account: estimate_account,
        SubAccount: estimate_subaccount
    }
    for k, v in mapping.items():
        if isinstance(instance, k):
            return v(instance, **kwargs)
    raise IntegrityError(
        "Unexpected instance %s - must be a valid Account/Sub Account."
        % instance.__class__.__name__
    )


def actualize_parent(instance, **kwargs):
    calculator_map = {
        Budget: actualize_budget,
        BudgetAccount: actualize_account,
        BudgetSubAccount: actualize_subaccount
    }
    calculator = calculator_map[type(instance)]
    calculator(instance, **kwargs)


@signals.any_fields_changed_receiver(fields=['unit', 'rate'], sender=Markup)
def markup_changed(instance, **kwargs):
    with signals.bulk_context:
        for obj in instance.children.all():
            estimate_instance(obj)


@dispatch.receiver(signals.m2m_changed, sender=Account.markups.through)
@dispatch.receiver(signals.m2m_changed, sender=SubAccount.markups.through)
def markups_changed(instance, reverse, action, **kwargs):
    if action in ('post_add', 'post_remove'):
        if reverse:
            objs = kwargs['model'].objects.filter(pk__in=kwargs['pk_set'])
            assert len(set([type(obj) for obj in objs])) in (0, 1)
            # The instance here is the Markup instance being added.
            with signals.bulk_context:
                for obj in objs:
                    estimate_instance(obj)
        else:
            # The instance here is the Account or SubAccount.
            estimate_instance(instance)


@dispatch.receiver(signals.pre_delete, sender=Markup)
def markup_deleted(instance, **kwargs):
    """
    When a :obj:`greenbudget.app.markup.models.Markup` instance is deleted,
    we need to both reactualize the parent of that instance and reestimate all
    models for which that :obj:`greenbudget.app.markup.models.Markup` is
    applied.

    Note that we have to use the pre_delete signal because we still need to
    determine which SubAccount(s) have to be reestimated.  We also have to
    explicitly define the Markup(s) for the reestimation, so it knows to
    exclude the Markup that is about to be deleted.
    """
    if isinstance(instance.parent, (Budget, BudgetAccount, BudgetSubAccount)):
        actualize_parent(instance.parent, markups_to_be_deleted=[instance.pk])
    with signals.bulk_context:
        for obj in instance.children.all():
            estimate_instance(obj, markups_to_be_deleted=[instance.pk])


@dispatch.receiver(signals.post_create, sender=Markup)
def markup_created(instance, **kwargs):
    if isinstance(instance.parent, (Budget, BudgetAccount, BudgetSubAccount)):
        actualize_parent(instance.parent)


@signals.any_fields_changed_receiver(
    fields=['object_id', 'content_type'],
    sender=Markup
)
def markup_parent_changed(instance, changes, **kwargs):
    parents_to_reactualize = []

    def mark_content_instance_change(*args, **kwargs):
        old_instance, new_instance = generic_foreign_key_instance_change(
            *args, **kwargs)
        if old_instance not in parents_to_reactualize \
                and old_instance is not None:
            parents_to_reactualize.append(old_instance)
        if new_instance not in parents_to_reactualize \
                and new_instance is not None:
            parents_to_reactualize.append(new_instance)

    # If the object_id and content_type were changed at the same time, we need
    # to handle that differently because they are fields that depend on one
    # another.  If the object_id was changed and the content_type was changed,
    # and we only address the object_id change first, we will most likely get
    # a ObjectDoesNotExist error when fetching the model based on the CT
    # with that object_id from the database.
    if changes.has_changes_for_fields('object_id', 'content_type'):
        obj_id_change = changes.get_change_for_field("object_id", strict=True)
        ct_change = changes.get_change_for_field("content_type", strict=True)
        mark_content_instance_change(
            instance,
            obj_id_change=obj_id_change,
            ct_change=ct_change
        )
        # Remove the mutually changed fields from the set of all changes
        # because they are already addressed.
        changes.remove_changes_for_fields('object_id', 'content_type')

    # Address any leftover changes that occurred that were not consistent with
    # an object_id - content_type simultaneous change.
    for change in changes:
        assert change.field in ('object_id', 'content_type')
        mark_content_instance_change(
            instance,
            obj_id_change=change if change.field == 'object_id' else None,
            ct_change=change if change.field == 'content_type' else None
        )

    for obj in parents_to_reactualize:
        if isinstance(obj, (Budget, BudgetAccount, BudgetSubAccount)):
            actualize_parent(obj)


@dispatch.receiver(signals.m2m_changed, sender=BudgetAccount.markups.through)
@dispatch.receiver(signals.m2m_changed, sender=BudgetSubAccount.markups.through)
def validate_markup_children(instance, reverse, action, **kwargs):
    if action == 'pre_add':
        # Depending on whether or not the M2M was changed on the forward or
        # reverse side of the field, the instance will refer to different
        # things.
        if reverse:
            # The instance here is the Markup instance being added.
            children = kwargs['model'].objects.filter(pk__in=kwargs['pk_set'])
            for child in children:
                if child.parent != instance.parent:
                    raise IntegrityError(
                        "Can only add markups to an instance that share "
                        "the same parent as the markups being added."
                    )
        else:
            # The instance here is the Account or SubAccount.
            markups = Markup.objects.filter(pk__in=kwargs['pk_set'])
            for markup in markups:
                if markup.parent != instance.parent:
                    raise IntegrityError(
                        "Can only add markups to an instance that share "
                        "the same parent as the markups being added."
                    )
