from django import dispatch
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError

from greenbudget.app import signals
from greenbudget.app.account.signals import actualize_account
from greenbudget.app.subaccount.models import BudgetSubAccount
from greenbudget.app.subaccount.signals import actualize_subaccount

from .models import Actual


def actualize_owner(owner, **kwargs):
    if isinstance(owner, BudgetSubAccount):
        actualize_subaccount(owner, **kwargs)
    else:
        # If the Actual is associated with a Markup instance, every Account
        # and/or SubAccount associated with that Markup instance must be
        # reactualized.  We do not have to actualize the Markup itself, because
        # it's actual value is calculated live with an @property.
        for account in owner.accounts.all():
            actualize_account(account, **kwargs)
        for subaccount in owner.subaccounts.all():
            actualize_subaccount(subaccount, **kwargs)


@dispatch.receiver(signals.post_create, sender=Actual)
def actual_created(instance, **kwargs):
    if instance.owner is not None:
        actualize_owner(instance.owner)


@dispatch.receiver(signals.pre_delete, sender=Actual)
def actual_deleted(instance, **kwargs):
    # Note that we have to use the pre_delete signal because we still need to
    # determine which SubAccount(s) have to be reactualized.  We also have to
    # explicitly define the Actuals(s) for the reactualization, so it knows to
    # exclude the Actual that is about to be deleted.
    if instance.owner is not None:
        actualize_owner(
            instance.owner,
            actuals_to_be_deleted=[instance.pk]
        )


@dispatch.receiver(signals.pre_save, sender=Actual)
def validate_actual(instance, **kwargs):
    if instance.owner is not None and instance.owner.budget != instance.budget:
        raise IntegrityError(
            "Can only add actuals with the same parent as the instance."
        )
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
def actual_metrics_changed(instance, **kwargs):
    objects_to_reactualize = []
    for change in kwargs['changes']:
        assert change.field in ('object_id', 'content_type', 'value')
        if change.field in ('object_id', 'content_type'):
            # The previous value of a FK will be the ID, not the full object -
            # for reasons explained in greenbudget.signals.models.
            if change.previous_value is not None:
                previous_ctype_id = instance.content_type_id
                if change.field == 'content_type':
                    previous_ctype_id = change.previous_value

                previous_object_id = instance.object_id
                if change.field == 'object_id':
                    previous_object_id = change.previous_value

                ct = ContentType.objects.get(pk=previous_ctype_id)
                model_cls = ct.model_class()
                previous_instance = model_cls.objects.get(
                    pk=previous_object_id)
                if previous_instance not in objects_to_reactualize:
                    objects_to_reactualize.append(previous_instance)

            if change.value is not None:
                ct = instance.content_type
                if change.field == 'content_type':
                    ct = change.value

                object_id = instance.object_id
                if change.field == 'object_id':
                    object_id = change.value

                model_cls = ct.model_class()
                instance = model_cls.objects.get(pk=object_id)
                if instance not in objects_to_reactualize:
                    objects_to_reactualize.append(instance)

        else:
            if instance.owner is not None \
                    and instance.owner not in objects_to_reactualize:
                objects_to_reactualize.append(instance.owner)

    for obj in objects_to_reactualize:
        actualize_owner(obj)
