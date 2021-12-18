from django import dispatch

from greenbudget.app import signals

from .mail import send_post_activation_email
from .models import User


@dispatch.receiver(signals.post_delete, sender=User)
def user_deleted(instance, **kwargs):
    instance.profile_image.delete(False)


@dispatch.receiver(signals.pre_save, sender=User)
def user_to_save(instance, **kwargs):
    if instance.is_superuser:
        instance.is_verified = True


@signals.field_changed_receiver('is_approved', sender=User)
def user_saved(instance, change, **kwargs):
    assert change.previous_value != change.value
    if change.value is True:
        send_post_activation_email(instance)
