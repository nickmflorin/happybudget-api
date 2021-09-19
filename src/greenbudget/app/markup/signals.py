import logging

from django import dispatch
from django.db import IntegrityError

from greenbudget.app import signals
from greenbudget.app.account.models import BudgetAccount
from greenbudget.app.account.signals import estimate_account
from greenbudget.app.group.models import Group
from greenbudget.app.subaccount.models import BudgetSubAccount
from greenbudget.app.subaccount.signals import estimate_subaccount

from .models import Markup
from .utils import get_surrounding_markups


logger = logging.getLogger('signals')


@dispatch.receiver(signals.m2m_changed, sender=BudgetAccount.markups.through)
@dispatch.receiver(signals.m2m_changed, sender=BudgetSubAccount.markups.through)
@dispatch.receiver(signals.m2m_changed, sender=Group.markups.through)
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


@signals.any_fields_changed_receiver(fields=['unit', 'rate'], sender=Markup)
def markup_changed(instance, **kwargs):
    with signals.bulk_context:
        for obj in instance.children.all():
            if isinstance(obj, BudgetAccount):
                estimate_account(obj)
            else:
                estimate_subaccount(obj)


@dispatch.receiver(signals.m2m_changed, sender=BudgetAccount.markups.through)
@dispatch.receiver(signals.m2m_changed, sender=BudgetSubAccount.markups.through)
def markups_changed(instance, reverse, action, **kwargs):
    estimator_map = {
        BudgetAccount: estimate_account,
        BudgetSubAccount: estimate_subaccount
    }
    if action in ('post_add', 'post_remove'):
        objs = kwargs['model'].objects.filter(pk__in=kwargs['pk_set'])
        assert len(set([type(obj) for obj in objs])) in (0, 1)

        if reverse:
            estimator = estimator_map[type(objs[0])]
            with signals.bulk_context:
                for obj in objs:
                    estimator(obj)

            # If a child object is removed from a Markup instance, it must also
            # be removed from all surrounding Markup instances.  Similiarly,
            # if a child object is added to a Markup instance, it must also
            # be added to all surrounding Markup instances.
            for obj in objs:
                surrounding = get_surrounding_markups(obj.parent, instance)
                with signals.m2m_changed.disable():
                    if action == 'post_remove':
                        obj.markups.remove(*surrounding)
                    else:
                        obj.markups.add(*surrounding)
        else:
            estimator = estimator_map[type(instance)]
            estimator(instance)

            # If a child object is removed from a Markup instance, it must also
            # be removed from all surrounding Markup instances.  Similiarly,
            # if a child object is added to a Markup instance, it must also
            # be added to all surrounding Markup instances.
            markups = kwargs['model'].objects.filter(
                pk__in=kwargs['pk_set'])
            surrounding = []
            for markup in markups:
                surrounding += get_surrounding_markups(instance.parent, markup)
            with signals.m2m_changed.disable():
                if action == 'post_remove':
                    instance.markups.remove(*surrounding)
                else:
                    instance.markups.add(*surrounding)


@dispatch.receiver(signals.pre_delete, sender=Markup)
def markup_deleted(instance, **kwargs):
    # Note that we have to use the pre_delete signal because we still need to
    # determine which SubAccount(s) have to be reestimated.  We also have to
    # explicitly define the Markup(s) for the reestimation, so it knows to
    # exclude the Markup that is about to be deleted.
    with signals.bulk_context:
        for obj in instance.children.all():
            if isinstance(obj, BudgetAccount):
                estimate_account(obj, markups_to_be_deleted=[instance.pk])
            else:
                estimate_subaccount(obj, markups_to_be_deleted=[instance.pk])


@dispatch.receiver(signals.m2m_changed, sender=Group.markups.through)
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
                elif isinstance(child, Group) and instance.group == child:
                    raise IntegrityError(
                        "A markup cannot both belong to a group and have the "
                        "same group as a child."
                    )
                # for child in [c for c in children if not isinstance(c, Group)]:
                #     validate_child_markups(child)
        else:
            # The instance here is the Group, Account or SubAccount.
            markups = Markup.objects.filter(pk__in=kwargs['pk_set'])
            for markup in markups:
                if markup.parent != instance.parent:
                    raise IntegrityError(
                        "Can only add markups to an instance that share "
                        "the same parent as the markups being added."
                    )
                elif isinstance(instance, Group) and markup.group == instance:
                    raise IntegrityError(
                        "A markup cannot both belong to a group and have the "
                        "same group as a child."
                    )
            # validate_child_markups(instance)
