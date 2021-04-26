from django import dispatch
from django.db.models.signals import post_save

from .models import BudgetSubAccount, TemplateSubAccount


@dispatch.receiver(post_save, sender=BudgetSubAccount)
@dispatch.receiver(post_save, sender=TemplateSubAccount)
def remove_parent_calculated_fields(instance, **kwargs):
    # If a SubAccount has children SubAccount(s), the fields used to derive
    # calculated values are no longer used since the calculated values are
    # derived from the children, not the attributes on that SubAccount.
    if isinstance(instance.parent, (BudgetSubAccount, TemplateSubAccount)):
        for field in instance.DERIVING_FIELDS:
            setattr(instance.parent, field, None)
        instance.parent.fringes.set([])
        instance.parent.save(track_changes=False)
