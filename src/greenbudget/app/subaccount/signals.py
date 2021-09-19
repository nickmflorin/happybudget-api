import logging

from django import dispatch
from django.contrib.contenttypes.models import ContentType

from greenbudget.app import signals
from greenbudget.app.account.signals import (
    estimate_account, actualize_account, calculate_account)

from .models import BudgetSubAccount, TemplateSubAccount


logger = logging.getLogger('signals')


@signals.bulk_context.handler(
    id=lambda instance: instance.pk,
    queue_in_context=True,
    side_effect=lambda instance, subaccounts_to_be_deleted: [
        signals.SideEffect(
            func=actualize_account,
            args=(instance.parent, ),
            kwargs={
                'subaccounts_to_be_deleted': subaccounts_to_be_deleted
            },
            # There are weird cases (like CASCADE deletes) where non-nullable
            # fields will be temporarily null - they just won't be saved in a
            # NULL state.
            conditional=instance.parent is not None and not isinstance(
                instance.parent, (BudgetSubAccount, TemplateSubAccount))
        ),
        signals.SideEffect(
            func=actualize_subaccount,
            args=(instance.parent, ),
            kwargs={
                'subaccounts_to_be_deleted': subaccounts_to_be_deleted
            },
            # There are weird cases (like CASCADE deletes) where non-nullable
            # fields will be temporarily null - they just won't be saved in a
            # NULL state.
            conditional=instance.parent is not None and isinstance(
                instance.parent, (BudgetSubAccount, TemplateSubAccount))
        )
    ]
)
def actualize_subaccount(instance, actuals_to_be_deleted=None,
        subaccounts_to_be_deleted=None):
    """
    Reactualizes the :obj:`greenbudget.app.subaccount.models.SubAccount` based
    on the :obj:`greenbudget.app.actual.models.Actual`(s) associated with the
    instance.
    """
    instance.establish_actual(
        actuals_to_be_deleted=actuals_to_be_deleted,
        subaccounts_to_be_deleted=subaccounts_to_be_deleted
    )
    instance.save(update_fields=["actual"], suppress_budget_update=True)


@signals.bulk_context.handler(
    id=lambda instance: instance.pk,
    queue_in_context=True,
    side_effect=lambda instance, subaccounts_to_be_deleted: [
        signals.SideEffect(
            func=estimate_account,
            args=(instance.parent, ),
            kwargs={
                'subaccounts_to_be_deleted': subaccounts_to_be_deleted
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
                'subaccounts_to_be_deleted': subaccounts_to_be_deleted
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
        markups_to_be_deleted=None, subaccounts_to_be_deleted=None):
    """
    Reestimates the :obj:`greenbudget.app.subaccount.models.SubAccount` based
    on the calculatable fields of the instance and the
    :obj:`greenbudget.app.fringe.models.Fringe`(s) associated with the instance.
    """
    instance.establish_all(
        markups_to_be_deleted=markups_to_be_deleted,
        fringes_to_be_deleted=fringes_to_be_deleted,
        subaccounts_to_be_deleted=subaccounts_to_be_deleted
    )
    instance.save(
        update_fields=[
            'estimated',
            'fringe_contribution',
            'markup_contribution'
        ],
        suppress_budget_update=True
    )


@signals.bulk_context.handler(
    id=lambda parent: parent.pk,
    # There are cases with CASCADE deletes where a non-nullable field will be
    # temporarily null.
    conditional=lambda parent: parent is not None,
    queue_in_context=True,
    side_effect=lambda parent, subaccounts_to_be_deleted: [
        signals.SideEffect(
            func=calculate_account,
            args=(parent,),
            kwargs={
                'subaccounts_to_be_deleted': subaccounts_to_be_deleted
            },
            conditional=not isinstance(
                parent, (BudgetSubAccount, TemplateSubAccount))
        ),
        signals.SideEffect(
            func=calculate_subaccount,
            args=(parent,),
            kwargs={
                'subaccounts_to_be_deleted': subaccounts_to_be_deleted
            },
            conditional=isinstance(
                parent, (BudgetSubAccount, TemplateSubAccount))
        )
    ]
)
def calculate_parent(parent, subaccounts_to_be_deleted=None):
    pass


@signals.bulk_context.handler(
    id=lambda instance: instance.pk,
    queue_in_context=True,
    side_effect=lambda instance, subaccounts_to_be_deleted: [
        signals.SideEffect(
            func=estimate_subaccount,
            args=(instance,),
            kwargs={
                'subaccounts_to_be_deleted': subaccounts_to_be_deleted
            },
        ),
        signals.SideEffect(
            func=actualize_subaccount,
            args=(instance, ),
            conditional=isinstance(instance, BudgetSubAccount),
            kwargs={
                'subaccounts_to_be_deleted': subaccounts_to_be_deleted
            },
        )
    ]
)
def calculate_subaccount(instance, subaccounts_to_be_deleted=None):
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
    calculate_parent(instance.parent, subaccounts_to_be_deleted=[instance.pk])


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

    if new_parent != previous_parent:
        calculate_parent(previous_parent)
        calculate_parent(new_parent)


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
