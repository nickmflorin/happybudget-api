from functools import partialmethod

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db import models


def get_models_for_fk_choices(model_cls, fk_field):
    if not hasattr(model_cls, fk_field) \
            or not isinstance(getattr(model_cls, fk_field).field, models.ForeignKey):  # noqa
        raise Exception(
            "No such ForeignKey field exists with name %s on model %s."
            % (fk_field, model_cls.__name__)
        )
    choices = getattr(model_cls, fk_field).field.remote_field.limit_choices_to
    return tuple([
        apps.get_model(app_label=ctype.app_label, model_name=ctype.model)
        for ctype in ContentType.objects.filter(choices)
    ])


class ModelHistoryTracker:

    def __init__(self, fields):
        if not fields:
            raise ValueError("Can't track zero fields")
        self.fields = set(fields)

    def contribute_to_class(self, cls, name):
        setattr(cls, '_get_field_history', _get_field_history)
        for field in self.fields:
            setattr(cls, 'get_%s_history' % field,
                    partialmethod(cls._get_field_history, field=field))
        self.name = name
        self.attname = '_%s' % name
        # models.signals.class_prepared.connect(self.finalize_class, sender=cls)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            return []


def _get_field_history(self, field):
    return []
