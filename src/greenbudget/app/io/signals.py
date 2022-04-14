from django import dispatch

from greenbudget.app import signals

from greenbudget.app.actual.models import Actual
from greenbudget.app.budget.cache import budget_actuals_cache
from greenbudget.app.contact.cache import user_contacts_cache
from greenbudget.app.contact.models import Contact
from greenbudget.app.subaccount.cache import (
    subaccount_instance_cache, invalidate_parent_children_cache)
from greenbudget.app.subaccount.models import BudgetSubAccount

from .models import Attachment


@dispatch.receiver(signals.post_delete, sender=Attachment)
def attachment_deleted(instance, **kwargs):
    instance.file.delete(False)


@dispatch.receiver(
    signal=signals.m2m_changed,
    sender=BudgetSubAccount.attachments.through
)
@dispatch.receiver(
    signal=signals.m2m_changed,
    sender=Actual.attachments.through
)
@dispatch.receiver(
    signal=signals.m2m_changed,
    sender=Contact.attachments.through
)
def attachments_changed(instance, reverse, action, model, pk_set, **kwargs):
    # For now, until we figure out how to appropriately handle multi-user
    # permissions in regard to attachments, the attachment owners must be
    # self consistent with the BudgetSubAccount, Actual or Contact owners.
    # Regardless of multi-user, this will always be the case for Contact(s),
    # since Contact(s) are not collaborative, but we will eventually need to
    # develop a better system around attachments of a BudgetSubAccount or Actual.
    if action in ('pre_add', 'pre_remove'):
        objs = model.objects.filter(pk__in=pk_set)
        for obj in objs:
            obj.has_same_owner(instance, raise_exception=True)

    elif action in ('post_add', 'post_remove'):
        if not reverse:
            attachments = model.objects.filter(pk__in=pk_set)
            related = [instance]
        else:
            related = model.objects.filter(pk__in=pk_set)
            attachments = [instance]

        if action == 'post_remove':
            for attachment in attachments:
                if attachment.is_empty():
                    attachment.delete()

        if any([isinstance(obj, Contact) for obj in related]):
            user_contacts_cache.invalidate()

        actuals = [obj for obj in related if isinstance(obj, Actual)]
        budgets = set([actual.budget for actual in actuals])
        budget_actuals_cache.invalidate(budgets)

        subaccounts = set([
            obj for obj in related if isinstance(obj, BudgetSubAccount)])
        subaccount_instance_cache.invalidate(subaccounts)
        invalidate_parent_children_cache(set([s.parent for s in subaccounts]))
