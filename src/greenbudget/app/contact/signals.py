from django import dispatch

from greenbudget.app import signals

from .cache import user_contacts_cache
from .models import Contact


@dispatch.receiver(signals.post_save, sender=Contact)
def contact_saved(instance, **kwargs):
    user_contacts_cache.invalidate(instance.user)


@dispatch.receiver(signals.post_delete, sender=Contact)
def contact_deleted(instance, **kwargs):
    if instance.intermittent_user is not None:
        user_contacts_cache.invalidate(instance.intermittent_user)
