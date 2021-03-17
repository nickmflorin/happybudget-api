from django.contrib.contenttypes.models import ContentType

from .models import Event


def model_can_be_tracked():
    choices = Event.content_type.field.remote_field.limit_choices_to


class ModelHistoryTracker:
    pass
