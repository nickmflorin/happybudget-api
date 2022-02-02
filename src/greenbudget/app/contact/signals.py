from django import dispatch

from greenbudget.app import signals

from .cache import user_contacts_cache
from .models import Contact


@dispatch.receiver(signals.pre_save, sender=Contact)
def contact_to_save(instance, **kwargs):
    user_contacts_cache.invalidate()
    if instance.order is None:
        instance.order_at_bottom()
    instance.validate_before_save()


@dispatch.receiver(signals.pre_delete, sender=Contact)
def contact_to_delete(instance, **kwargs):
    user_contacts_cache.invalidate()
