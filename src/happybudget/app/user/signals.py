from django import dispatch

from happybudget.app import signals

from .models import User


@dispatch.receiver(signals.post_delete, sender=User)
def user_deleted(instance, **kwargs):
    # TODO: We also need to remove Stripe related data when the User is deleted.
    instance.profile_image.delete(False)
