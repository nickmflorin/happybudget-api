from django import dispatch
from django.db.models.signals import post_save

from .models import SubAccount


@dispatch.receiver(post_save, sender=SubAccount)
def remove_parent_calculated_fields(instance, **kwargs):
    # If a SubAccount has children SubAccount(s), the fields used to derive
    # calculated values are no longer used since the calculated values are
    # derived from the children, not the attributes on that SubAccount.
    for field in instance.DERIVING_FIELDS:
        print("Setting field %s to None on %s." %
              (field, instance.content_object.pk))
        setattr(instance.content_object, field, None)
    instance.content_object.save()
