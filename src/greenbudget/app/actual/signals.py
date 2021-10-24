from django import dispatch
from django.db import IntegrityError

from greenbudget.app import signals
from greenbudget.app.account.models import BudgetAccount
from greenbudget.app.budget.models import Budget
from greenbudget.app.budget.signals import actualize_budget
from greenbudget.app.signals.utils import generic_foreign_key_instance_change
from greenbudget.app.account.signals import actualize_account
from greenbudget.app.subaccount.models import BudgetSubAccount
from greenbudget.app.subaccount.signals import actualize_subaccount
from greenbudget.app.markup.models import Markup

from .models import Actual


def actualize_owner(owner):
    assert isinstance(owner, (BudgetSubAccount, Markup))
    if isinstance(owner, BudgetSubAccount):
        actualize_subaccount(owner)
    else:
        # If the Actual is associated with a Markup instance, the parent of
        # that Markup instance must be reactualized. We do not have to actualize
        # the Markup itself, because it's actual value is calculated live with
        # an @property.
        assert isinstance(owner.parent, (Budget, BudgetAccount, BudgetSubAccount))  # noqa
        if isinstance(owner.parent, Budget):
            actualize_budget(owner.parent)
        elif isinstance(owner.parent, BudgetAccount):
            actualize_account(owner.parent)
        else:
            actualize_subaccount(owner.parent)


@dispatch.receiver(signals.post_create, sender=Actual)
def actual_created(instance, **kwargs):
    if instance.owner is not None:
        actualize_owner(instance.owner)


@dispatch.receiver(signals.post_delete, sender=Actual)
def actual_deleted(instance, **kwargs):
    if instance.owner is not None:
        actualize_owner(instance.owner)


@dispatch.receiver(signals.pre_save, sender=Actual)
def validate_actual(instance, **kwargs):
    try:
        budget = instance.budget
    except Actual.budget.RelatedObjectDoesNotExist:
        pass
    else:
        if instance.owner is not None and instance.owner.budget != budget:
            raise IntegrityError(
                "Can only add actuals with the same parent as the instance.")
        elif instance.contact is not None \
                and instance.contact.user != instance.created_by:
            raise IntegrityError(
                "Cannot assign a contact created by one user to an actual "
                "created by another user."
            )


@signals.any_fields_changed_receiver(
    fields=['value', 'object_id', 'content_type'],
    sender=Actual
)
def actual_metrics_changed(instance, changes, **kwargs):
    objects_to_reactualize = []

    def mark_content_instance_change(*args, **kwargs):
        old_instance, new_instance = generic_foreign_key_instance_change(
            *args, **kwargs)
        if old_instance not in objects_to_reactualize \
                and old_instance is not None:
            objects_to_reactualize.append(old_instance)
        if new_instance not in objects_to_reactualize \
                and new_instance is not None:
            objects_to_reactualize.append(new_instance)

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
            ct_change=ct_change,
            assert_models=(BudgetSubAccount, Markup)
        )
        # Remove the mutually changed fields from the set of all changes
        # because they are already addressed.
        changes.remove_changes_for_fields('object_id', 'content_type')

    # Address any leftover changes that occurred that were not consistent with
    # an object_id - content_type simultaneous change.
    for change in changes:
        assert change.field in ('object_id', 'content_type', 'value')
        if change.field in ('object_id', 'content_type'):
            mark_content_instance_change(
                instance,
                obj_id_change=change if change.field == 'object_id' else None,
                ct_change=change if change.field == 'content_type' else None,
                assert_models=(BudgetSubAccount, Markup)
            )
        else:
            if instance.owner is not None \
                    and instance.owner not in objects_to_reactualize:
                objects_to_reactualize.append(instance.owner)

    for obj in objects_to_reactualize:
        actualize_owner(obj)
