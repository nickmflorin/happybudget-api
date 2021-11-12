from django import dispatch
from django.db import IntegrityError

from greenbudget.app import signals
from .models import Template


@dispatch.receiver(signals.pre_save, sender=Template)
def template_to_save(instance, **kwargs):
    if instance.community is True and not instance.created_by.is_staff:
        raise IntegrityError(
            "Community templates can only be created by staff users.")
