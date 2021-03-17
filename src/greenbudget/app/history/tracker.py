from copy import deepcopy
from functools import partialmethod
import threading

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db import models

from .models import Event, FieldAlterationEvent


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


class ModelInstanceTracker(object):
    def __init__(self, instance, fields):
        self.instance = instance
        self.fields = fields

    def get_field_value(self, field):
        return getattr(self.instance, field)

    def set_saved_fields(self, fields=None):
        if not self.instance.pk:
            self.saved_data = {}
        elif not fields:
            self.saved_data = self.current()

        for field, field_value in self.saved_data.items():
            self.saved_data[field] = deepcopy(field_value)

    def current(self, fields=None):
        if fields is None:
            fields = self.fields
        return dict((f, getattr(self.instance, f)) for f in fields)

    def has_changed(self, field):
        return self.previous(field) != getattr(self.instance, field)

    def previous(self, field):
        return self.saved_data.get(field)


class ModelHistoryTracker:
    """
    Credit due where credit is due - most of this was adopted from an existing
    package:

    https://github.com/grantmcconnaughey/django-field-history
    """
    tracker_class = ModelInstanceTracker
    thread = threading.local()

    def __init__(self, fields):
        assert len(fields) != 0, "Must provide at least 1 field to track."
        self.fields = set(fields)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            return Event.objects.get_for_model(instance)

    def contribute_to_class(self, cls, name):
        for field in self.fields:
            if not hasattr(cls, field) or not isinstance(
                    getattr(cls, field), (models.CharField, models.DecimalField)):  # noqa
                raise Exception("Invalid/unsupported field %s." % field)

        allowed_models = get_models_for_fk_choices(Event, "content_type")
        if cls not in allowed_models:
            raise Exception(
                "Cannot track history of model %s because it is not yet "
                "supported by the Event model." % cls.__name__
            )

        setattr(cls, '_get_field_events', _get_field_events)
        for field_name in self.fields:
            field = getattr(cls, field_name)
            setattr(cls, 'get_%s_events' % field_name,
                partialmethod(cls._get_char_field_events, field=field))

        self.name = name
        self.attname = '_%s' % name
        models.signals.class_prepared.connect(self.finalize_class, sender=cls)

    def finalize_class(self, sender, **kwargs):
        self.fields = self.fields
        models.signals.post_init.connect(self.initialize_tracker)
        self.model_class = sender
        setattr(sender, self.name, self)

    def initialize_tracker(self, sender, instance, **kwargs):
        # Only initialize instances of the given model (including children).
        if not isinstance(instance, self.model_class):
            return
        self._initialize_tracker(instance)
        # Patch the model's default save method to also create instances of
        # Event when appropriate.
        self.patch_save(instance)

    def _initialize_tracker(self, instance):
        tracker = self.tracker_class(instance, self.fields)
        setattr(instance, self.attname, tracker)
        tracker.set_saved_fields()

    def patch_save(self, instance):
        original_save = instance.save

        def save(**kwargs):
            is_new_object = instance.pk is None
            ret = original_save(**kwargs)
            tracker = getattr(instance, self.attname)

            events = []
            for field_name in self.fields:
                if tracker.has_changed(field_name) or is_new_object:
                    user = self.get_request_user()

                    old_value = tracker.previous(field_name)
                    if old_value is not None:
                        old_value = "%s" % old_value

                    new_value = tracker.get_field_value(field_name)
                    if new_value is not None:
                        new_value = "%s" % new_value

                    events.append(FieldAlterationEvent(
                        object=instance,
                        field=field_name,
                        old_value=old_value,
                        new_value=new_value,
                        user=user,
                    ))

            if events:
                FieldAlterationEvent.objects.bulk_create(events)

            # Update tracker in case this model is saved again
            self._initialize_tracker(instance)

            return ret

        instance.save = save

    def get_request_user(self):
        user = self.thread.request.user
        if not user.is_authenticated:
            raise Exception(
                "User should be authenticated to perform read/write operations!")  # noqa
        return user


def _get_field_events(self, field):
    return FieldAlterationEvent.objects.get_for_model_and_field(self, field)
