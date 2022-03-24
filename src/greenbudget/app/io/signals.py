from django import dispatch
from django.db import IntegrityError

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
    def validate(attachment, obj):
        if obj.created_by != attachment.created_by:
            raise IntegrityError(
                "Attachment %s was not created by the same user that the "
                "%s %s was." % (attachment.pk, obj.__class__.__name__, obj.pk)
            )

    if action in ('pre_add', 'pre_remove'):
        objs = model.objects.filter(pk__in=pk_set)
        # pylint: disable=expression-not-assigned
        if reverse:
            [validate(instance, obj) for obj in objs]
        else:
            [validate(obj, instance) for obj in objs]

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
