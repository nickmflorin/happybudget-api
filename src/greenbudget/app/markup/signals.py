import logging

from django import dispatch
from django.db import IntegrityError

from happybudget.lib.django_utils.models import generic_fk_instance_change

from happybudget.app import signals
from happybudget.app.account.models import Account
from happybudget.app.subaccount.models import SubAccount

from .models import Markup


logger = logging.getLogger('happybudget')


def get_children_to_reestimate_on_save(markup):
    """
    If :obj:`Markup` has a non-null value for `rate`, then the
    :obj:`Markup`'s will have a contribution to the estimated values of it's
    children, whether the children be instances of :obj:`Account` or
    :obj:SubAccount`, has changed.

    This means that when a :obj:`Markup` is just created or it's values for
    `rate` and/or `unit` have changed, it's children have to be reestimated.

    This method looks at an instance of :obj:`Markup` and returns the
    children that need to be reestimated as a result of a change to the
    :obj:`Markup` or the creation of the :obj:`Markup`.
    """
    # If the Markup is in the midst of being created, we always want
    # to estimate the children.
    if markup._state.adding is True or markup.was_just_added() \
            or markup.fields_have_changed('unit', 'rate'):
        return set(
            list(markup.accounts.all()) + list(markup.subaccounts.all()))
    return set()


def get_parents_to_reestimate_on_save(markup):
    """
    If :obj:`Markup` has a non-null value for `rate`, that :obj:`Markup`
    will have a contribution to the estimated values of it's parent, whether
    that parent be a :obj:`BaseBudget`, :obj:`Account` or :obj:`SubAccount`.

    This means that whenever a :obj:`Markup` is added, it's parent is
    changed or it's `unit` or `rate` fields have changed, the parent needs
    to be reestimated.  In the case that the parent has changed, both the
    new and old parent need to be reesetimated.

    This method looks at an instance of :obj:`Markup` and returns the parent
    or parents (in the case that the parent has changed) that need to be
    reestimated as a result of a change to the :obj:`Markup` or the
    creation of the :obj:`Markup`.
    """
    parents_to_reestimate = set([])
    # If the Markup is in the midst of being created, we always want
    # to estimate the parent.
    if markup._state.adding is True or markup.was_just_added():
        assert markup.parent is not None
        parents_to_reestimate.add(markup.parent)
    else:
        # We only need to reestimate the parent if the parent was changed
        # or the markup unit or rate was changed.
        old_parent, new_parent = generic_fk_instance_change(markup)
        if old_parent != new_parent:
            parents_to_reestimate.update([
                x for x in [old_parent, new_parent]
                if x is not None
            ])
        elif markup.fields_have_changed('unit', 'rate') \
                and markup.parent is not None:
            parents_to_reestimate.add(markup.parent)
    return parents_to_reestimate


@dispatch.receiver(signals.post_save, sender=Markup)
def markup_saved(instance, **kwargs):
    old_parent = None
    old, new = generic_fk_instance_change(instance)
    if old != new:
        old_parent = old

    Markup.objects.invalidate_related_caches(instance, old_parent=old_parent)

    # We must reestimate the associated models before we remove the children
    # (in the last code block) because we will need to know what the previously
    # associated models were in the case that the unit changes to FLAT (and no
    # longer has any children).
    to_reestimate = get_parents_to_reestimate_on_save(instance)
    to_reestimate.update(get_children_to_reestimate_on_save(instance))
    Markup.objects.bulk_estimate_all(to_reestimate, **kwargs)

    # Flat Markup(s) are not allowed to have children, so if the unit was
    # changed to Flat we need to remove the children.  Since we already
    # invalidated the Markup caches for each individual child, we do not
    # have to do this again.
    if instance.unit == Markup.UNITS.flat and instance.field_has_changed('unit'):
        with signals.disable():
            instance.clear_children()


@dispatch.receiver(signals.m2m_changed, sender=Account.markups.through)
@dispatch.receiver(signals.m2m_changed, sender=SubAccount.markups.through)
def markups_changed(instance, reverse, action, model, pk_set, **kwargs):
    def validate_parent(a, b):
        if a.parent != b.parent:
            raise IntegrityError(
                "Can only add markups to an instance that share "
                "the same parent as the markups being added."
            )

    def validate_unit(obj):
        if obj.unit != Markup.UNITS.percent:
            raise IntegrityError(
                "Can only add markups with unit `percent` as children of "
                "an Account/SubAccount."
            )

    if reverse:
        # The instance here is the Markup instance being added or removed.
        children = model.objects.filter(pk__in=pk_set)
        markups = [instance]
    else:
        # The instance here is the Account or SubAccount.  A Markup can belong
        # to several Account(s) or SubAccount(s).
        markups = Markup.objects.filter(pk__in=pk_set)
        children = [instance]

    # After Markups are added or removed from an Account/SubAccount, the
    # associated Account/SubAccount must be reestimated.
    if action in ('post_add', 'post_remove'):
        SubAccount.objects.bulk_estimate_all(children)

        if action == 'post_remove':
            # After Markups are removed from an Account/SubAcccount, we must
            # clean up empty Markup instances.
            markups_to_delete = []
            for markup in markups:
                if markup.is_empty and markup.unit == Markup.UNITS.percent:
                    logger.info(
                        "Deleting markup %s after it was removed because the "
                        "markup no longer has any children."
                        % markup.pk
                    )
                    markups_to_delete.append(markup)

            # Do not raise exceptions if Markup being deleted no longer exists
            # because we have to be concerned with race conditions.
            Markup.objects.bulk_delete(markups_to_delete, strict=False)

    elif action == 'pre_add':
        # Before Markup's are added or removed to an Account/SubAccount, we must
        # ensure that
        # (1) The Markup has the same parent as that Account/SubAccount, other
        #     wise the Markup will not appear in the correct place in the Budget.
        # (2) The Markup is of UNIT type PERCENT - because only PERCENT UNIT
        #     Markup(s) are applicable for children.
        # pylint: disable=expression-not-assigned
        [validate_unit(markup) for markup in markups]
        if reverse:
            [validate_parent(instance, child) for child in children]
        else:
            [validate_parent(markup, instance) for markup in markups]


@dispatch.receiver(signals.pre_delete, sender=Markup)
def markup_to_delete(instance, **kwargs):
    Markup.objects.invalidate_related_caches(instance)

    # If the Markup is being deleted as a part of a CASCADE delete from it's
    # parent, do not reestimate related objects as they will be being deleted.
    if not instance.parent.is_deleting:
        to_reestimate = set([instance.parent])
        to_reestimate.update(set(
            list(instance.accounts.all()) + list(instance.subaccounts.all())))
        Markup.objects.bulk_estimate_all(
            to_reestimate, markups_to_be_deleted=[instance.pk])

        if instance.parent.domain == 'budget':
            Markup.objects.bulk_actualize_all(
                instance.parent, markups_to_be_deleted=[instance.pk])
