from django import dispatch

from greenbudget.app import signals

from .cache import user_contacts_cache
from .models import Contact


@dispatch.receiver(signals.pre_save, sender=Contact)
def contact_to_save(instance, **kwargs):
    instance.validate_before_save()


@dispatch.receiver(signals.post_save, sender=Contact)
def contact_saved(instance, **kwargs):
    user_contacts_cache.invalidate(instance.created_by)


@dispatch.receiver(signals.pre_delete, sender=Contact)
def contact_to_delete(instance, **kwargs):
    user_contacts_cache.invalidate(instance.created_by)
