from django import dispatch
from django.db import IntegrityError

from greenbudget.app import signals

from greenbudget.app.actual.models import Actual
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
def attachments_to_changed(instance, reverse, action, **kwargs):
    def validate(attachment, obj):
        if obj.created_by != attachment.created_by:
            raise IntegrityError(
                "Attachment %s was not created by the same user that the "
                "SubAccount %s was." % (attachment.pk, obj.pk)
            )
    if action in ('pre_add', 'pre_remove'):
        objs = kwargs['model'].objects.filter(pk__in=kwargs['pk_set'])
        if reverse:
            [validate(instance, obj) for obj in objs]
        else:
            [validate(obj, instance) for obj in objs]
