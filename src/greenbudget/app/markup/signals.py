import logging

from django import dispatch
from django.db import IntegrityError

from greenbudget.app import signals
from greenbudget.app.account.models import BudgetAccount
from greenbudget.app.account.signals import calculate_account, estimate_account
from greenbudget.app.subaccount.models import BudgetSubAccount
from greenbudget.app.subaccount.signals import (
    calculate_subaccount, estimate_subaccount)

from .models import Markup


logger = logging.getLogger('signals')


@dispatch.receiver(signals.m2m_changed, sender=BudgetAccount.markups.through)
@dispatch.receiver(signals.m2m_changed, sender=BudgetSubAccount.markups.through)
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
    calculator_map = {
        BudgetAccount: estimate_account,
        BudgetSubAccount: estimate_subaccount
    }
    calculator = calculator_map[type(instance)]
    calculator(instance, **kwargs)


def calculate_instance(instance, **kwargs):
    calculator_map = {
        BudgetAccount: calculate_account,
        BudgetSubAccount: calculate_subaccount
    }
    calculator = calculator_map[type(instance)]
    calculator(instance, **kwargs)


@signals.any_fields_changed_receiver(fields=['unit', 'rate'], sender=Markup)
def markup_changed(instance, **kwargs):
    with signals.bulk_context:
        for obj in instance.children.all():
            estimate_instance(obj)


@dispatch.receiver(signals.m2m_changed, sender=BudgetAccount.markups.through)
@dispatch.receiver(signals.m2m_changed, sender=BudgetSubAccount.markups.through)
def markups_changed(instance, reverse, action, **kwargs):
    if action in ('post_add', 'post_remove'):
        if reverse:
            objs = kwargs['model'].objects.filter(pk__in=kwargs['pk_set'])
            assert len(set([type(obj) for obj in objs])) in (0, 1)
            # The instance here is the Markup instance being added.
            with signals.bulk_context:
                for obj in objs:
                    calculate_instance(obj)
        else:
            # The instance here is the Account or SubAccount.
            calculate_instance(instance)


@dispatch.receiver(signals.pre_delete, sender=Markup)
def markup_deleted(instance, **kwargs):
    # Note that we have to use the pre_delete signal because we still need to
    # determine which SubAccount(s) have to be reestimated.  We also have to
    # explicitly define the Markup(s) for the reestimation, so it knows to
    # exclude the Markup that is about to be deleted.
    with signals.bulk_context:
        for obj in instance.children.all():
            calculate_instance(obj, markups_to_be_deleted=[instance.pk])


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
