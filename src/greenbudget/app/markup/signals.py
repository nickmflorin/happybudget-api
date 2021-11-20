import logging

from django import dispatch
from django.db import IntegrityError

from greenbudget.app import signals
from greenbudget.app.account.models import Account
from greenbudget.app.budget.cache import budget_actuals_owner_tree_cache
from greenbudget.app.subaccount.models import SubAccount

from .models import Markup


logger = logging.getLogger('signals')


# NOTE: IF we start bulk updating Markup(s), then we need to apply this logic
# in the managers as well.
@dispatch.receiver(signals.post_save, sender=Markup)
def markup_saved(instance, **kwargs):
    # We must reestimate the associated models before we remove the children
    # because we will need to know what the previous associated models were
    # if the unit changes to FLAT.
    Markup.objects.reestimate_associated(instance)

    if instance.budget.domain == 'budget':
        budget_actuals_owner_tree_cache.invalidate(instance.budget)

    # Invalidate the caches that contain information about the Markup.
    for child in instance.children.all():
        child.parent.invalidate_markups_cache()

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
        # The instance here is the Account or SubAccount.
        markups = Markup.objects.filter(pk__in=pk_set)
        children = [instance]

    # After Markups are added or removed from an Account/SubAccount, the
    # associated Account/SubAccount must be reestimated.
    if action in ('post_add', 'post_remove'):
        SubAccount.objects.bulk_estimate_all(children)

        # After Markups are removed from an Account/SubAcccount, we must clean up
        # empty Markup instances.
        if action == 'post_remove':
            markups_to_delete = []
            for markup in markups:
                if markup.is_empty and markup.unit == Markup.UNITS.percent:
                    logger.info(
                        "Deleting markup %s after it was removed because the "
                        "markup no longer has any children."
                        % markup.pk
                    )
                    markups_to_delete.append(markup)
            Markup.objects.bulk_delete(markups_to_delete, strict=False)

            budgets = set([mk.budget for mk in markups_to_delete])
            budgets = [b for b in budgets if b.domain == 'budget']
            budget_actuals_owner_tree_cache.invalidate(budgets)

    # Before Markup's are added or removed to an Account/SubAccount, we must
    # ensure that the Markup has the same parent as that Account/SubAccount.
    elif action == 'pre_add':
        [validate_unit(markup) for markup in markups]
        if reverse:
            [validate_parent(instance, child) for child in children]
        else:
            [validate_parent(markup, instance) for markup in markups]


@dispatch.receiver(signals.pre_delete, sender=Markup)
def markup_to_be_deleted(instance, **kwargs):
    Markup.objects.pre_delete([instance])
