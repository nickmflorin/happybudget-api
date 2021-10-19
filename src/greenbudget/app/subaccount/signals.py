import logging

from django import dispatch
from django.db import IntegrityError

from greenbudget.app import signals
from greenbudget.app.account.models import BudgetAccount, TemplateAccount
from greenbudget.app.account.signals import (
    estimate_account, actualize_account, calculate_account)
from greenbudget.app.signals.utils import generic_foreign_key_instance_change

from .models import BudgetSubAccount, TemplateSubAccount


logger = logging.getLogger('signals')


def actualize_parent_conditional(instance, parents):
    # There are weird cases (like CASCADE deletes) where non-nullable
    # fields will be temporarily null - they just won't be saved in a
    # NULL state.
    correct_parent = instance.parent is not None \
        and isinstance(instance.parent, parents)
    change_occured = instance.actual != instance.previous_value('actual')
    return correct_parent and change_occured


@signals.bulk_context.handler(
    id=lambda instance: instance.pk,
    queue_in_context=True,
    side_effect=lambda instance, children_to_be_deleted: [
        signals.SideEffect(
            func=actualize_account,
            args=(instance.parent, ),
            kwargs={
                # We do not need to include the Markup(s) that will be deleted
                # because the Markup(s) will not belong to the parent, only the
                # instance being changed.
                'children_to_be_deleted': children_to_be_deleted
            },
            conditional=actualize_parent_conditional(
                instance, (BudgetAccount, TemplateAccount))
        ),
        signals.SideEffect(
            func=actualize_subaccount,
            args=(instance.parent, ),
            kwargs={
                # We do not need to include the Markup(s) that will be deleted
                # because the Markup(s) will not belong to the parent, only the
                # instance being changed.
                'children_to_be_deleted': children_to_be_deleted
            },
            conditional=actualize_parent_conditional(
                instance, (BudgetSubAccount, TemplateSubAccount))
        )
    ]
)
def actualize_subaccount(instance, actuals_to_be_deleted=None,
        children_to_be_deleted=None, markups_to_be_deleted=None):
    """
    Reactualizes the :obj:`greenbudget.app.subaccount.models.SubAccount` based
    on the :obj:`greenbudget.app.actual.models.Actual`(s) associated with the
    instance.
    """
    instance.actualize(
        actuals_to_be_deleted=actuals_to_be_deleted,
        children_to_be_deleted=children_to_be_deleted,
        markups_to_be_deleted=markups_to_be_deleted
    )
    if instance.actual != instance.previous_value('actual'):
        instance.save(update_fields=["actual"], suppress_budget_update=True)


@signals.bulk_context.handler(
    id=lambda instance: instance.pk,
    queue_in_context=True,
    side_effect=lambda instance, children_to_be_deleted: [
        signals.SideEffect(
            func=estimate_account,
            args=(instance.parent, ),
            kwargs={
                # We do not need to include the Markup(s) that will be deleted
                # because the Markup(s) will not belong to the parent, only the
                # instance being changed.
                'children_to_be_deleted': children_to_be_deleted
            },
            # There are weird cases (like CASCADE deletes) where non-nullable
            # fields will be temporarily null - they just won't be saved in a
            # NULL state.
            conditional=instance.parent is not None and not isinstance(
                instance.parent, (BudgetSubAccount, TemplateSubAccount))
        ),
        signals.SideEffect(
            func=estimate_subaccount,
            args=(instance.parent, ),
            kwargs={
                # We do not need to include the Markup(s) that will be deleted
                # because the Markup(s) will not belong to the parent, only the
                # instance being changed.
                'children_to_be_deleted': children_to_be_deleted
            },
            # There are weird cases (like CASCADE deletes) where non-nullable
            # fields will be temporarily null - they just won't be saved in a
            # NULL state.
            conditional=instance.parent is not None and isinstance(
                instance.parent, (BudgetSubAccount, TemplateSubAccount))
        )
    ]
)
def estimate_subaccount(instance, fringes_to_be_deleted=None,
        markups_to_be_deleted=None, children_to_be_deleted=None):
    """
    Reestimates the :obj:`greenbudget.app.subaccount.models.SubAccount` based
    on the calculatable fields of the instance and the
    :obj:`greenbudget.app.fringe.models.Fringe`(s) associated with the instance.
    """
    instance.estimate(
        markups_to_be_deleted=markups_to_be_deleted,
        fringes_to_be_deleted=fringes_to_be_deleted,
        children_to_be_deleted=children_to_be_deleted
    )
    instance.save(
        update_fields=list(instance.ESTIMATED_FIELDS),
        suppress_budget_update=True
    )


@signals.bulk_context.handler(
    id=lambda parent: parent.pk,
    # There are cases with CASCADE deletes where a non-nullable field will be
    # temporarily null.
    conditional=lambda parent: parent is not None,
    queue_in_context=True,
    side_effect=lambda parent, children_to_be_deleted: [
        signals.SideEffect(
            func=calculate_account,
            args=(parent,),
            kwargs={
                'children_to_be_deleted': children_to_be_deleted
            },
            conditional=not isinstance(
                parent, (BudgetSubAccount, TemplateSubAccount))
        ),
        signals.SideEffect(
            func=calculate_subaccount,
            args=(parent,),
            kwargs={
                'children_to_be_deleted': children_to_be_deleted
            },
            conditional=isinstance(
                parent, (BudgetSubAccount, TemplateSubAccount))
        )
    ]
)
def calculate_parent(parent, children_to_be_deleted=None):
    pass


@signals.bulk_context.handler(
    id=lambda instance: instance.pk,
    queue_in_context=True,
    side_effect=lambda instance, children_to_be_deleted, markups_to_be_deleted: [  # noqa
        signals.SideEffect(
            func=estimate_subaccount,
            args=(instance,),
            kwargs={
                'children_to_be_deleted': children_to_be_deleted,
                'markups_to_be_deleted': markups_to_be_deleted
            },
        ),
        signals.SideEffect(
            func=actualize_subaccount,
            args=(instance, ),
            conditional=isinstance(instance, BudgetSubAccount),
            kwargs={
                'children_to_be_deleted': children_to_be_deleted,
                'markups_to_be_deleted': markups_to_be_deleted
            },
        )
    ]
)
def calculate_subaccount(instance, children_to_be_deleted=None,
        markups_to_be_deleted=None):
    pass


@signals.any_fields_changed_receiver(
    fields=['rate', 'multiplier', 'quantity'],
    sender=BudgetSubAccount
)
@signals.any_fields_changed_receiver(
    fields=['rate', 'multiplier', 'quantity'],
    sender=TemplateSubAccount
)
def subaccount_reestimation(instance, **kwargs):
    if instance.children.count() == 0:
        estimate_subaccount(instance)


@dispatch.receiver(signals.post_create, sender=BudgetSubAccount)
@dispatch.receiver(signals.post_create, sender=TemplateSubAccount)
def subaccount_created(instance, **kwargs):
    calculate_subaccount(instance)


@dispatch.receiver(signals.post_delete, sender=BudgetSubAccount)
@dispatch.receiver(signals.post_delete, sender=TemplateSubAccount)
def subaccount_deleted(instance, **kwargs):
    calculate_parent(instance.parent, children_to_be_deleted=[instance.pk])


@signals.any_fields_changed_receiver(
    fields=['object_id', 'content_type'],
    sender=BudgetSubAccount
)
@signals.any_fields_changed_receiver(
    fields=['object_id', 'content_type'],
    sender=TemplateSubAccount
)
def subaccount_parent_changed(instance, changes, **kwargs):
    parents_to_recalculate = []

    def mark_content_instance_change(*args, **kwargs):
        old_instance, new_instance = generic_foreign_key_instance_change(
            *args, **kwargs)
        if old_instance not in parents_to_recalculate \
                and old_instance is not None:
            parents_to_recalculate.append(old_instance)
        if new_instance not in parents_to_recalculate \
                and new_instance is not None:
            parents_to_recalculate.append(new_instance)

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

    for obj in parents_to_recalculate:
        calculate_parent(obj)


@dispatch.receiver(signals.pre_save, sender=BudgetSubAccount)
def validate_subaccount(instance, **kwargs):
    if instance.contact is not None \
            and instance.contact.user != instance.created_by:
        raise IntegrityError(
            "Cannot assign a contact created by one user to a sub account "
            "created by another user."
        )


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
