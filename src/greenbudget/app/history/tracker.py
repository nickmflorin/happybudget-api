from copy import deepcopy
import datetime
from functools import partialmethod
import json
import logging
import threading

from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models

from greenbudget.lib.utils.dateutils import api_datetime_string

from .models import Event, FieldAlterationEvent, CreateEvent


logger = logging.getLogger('backend')

SUPPORTED_FIELDS = (
    models.CharField,
    models.FloatField,
    models.IntegerField,
    models.DateTimeField
)


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

    def set_saved_fields(self):
        self.saved_data = dict(
            (f, deepcopy(getattr(self.instance, f))) for f in self.fields)

    def has_changed(self, field):
        return self.saved_data.get(field) != getattr(self.instance, field)


class ModelHistoryTracker:
    """
    Credit due where credit is due - some of this was adopted from an existing
    package:

    https://github.com/grantmcconnaughey/django-field-history
    """
    tracker_class = ModelInstanceTracker
    thread = threading.local()

    def __init__(self, fields, user_field=None):
        assert len(fields) != 0, "Must provide at least 1 field to track."
        self.fields = set(fields)
        # This field is used to get the associated User off of the model
        # being tracked ONLY in the case that there is not an active request
        # (and thus, a user attached to the request).  We really only have to
        # worry about this when performing tests, since model write operations
        # will always be performed in the presence of a request.
        self._user_field = user_field

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            return Event.objects.get_for_model(instance)

    def contribute_to_class(self, cls, name):
        # Do not track the model history if the settings do not explicitly turn
        # it on.
        if getattr(settings, 'TRACK_MODEL_HISTORY', False) is False:
            logger.info(
                "Suppressing model tracking behavior for %s - "
                "`settings.TRACK_MODEL_HISTORY` is either not defined or False."
                % cls.__name__
            )
            return

        # Make sure the fields we are tracking are supported.
        for field in self.fields:
            if not hasattr(cls, field) or not isinstance(
                    getattr(cls, field).field, SUPPORTED_FIELDS):
                raise Exception("Invalid/unsupported field %s." % field)

        setattr(cls, '_get_field_events', _get_field_events)
        for field_name in self.fields:
            field = getattr(cls, field_name)
            setattr(cls, 'get_%s_events' % field_name,
                partialmethod(cls._get_field_events, field=field))

        self.name = name
        models.signals.class_prepared.connect(self.finalize_class, sender=cls)

    def finalize_class(self, sender, **kwargs):
        models.signals.post_init.connect(self.post_init, sender=sender)
        models.signals.post_save.connect(self.post_save, sender=sender)
        setattr(sender, self.name, self)

    def post_init(self, sender, instance, **kwargs):
        self.initialize_tracker(instance)
        # Patch the model's default save and delete methods to also create
        # instances of Event when appropriate.
        self.patch_save(instance)

    def post_save(self, sender, instance, **kwargs):
        if kwargs['created'] is True and instance._record_history is True:
            CreateEvent.objects.create(
                content_object=instance,
                user=self.get_event_user(instance),
            )

    def initialize_tracker(self, instance):
        tracker = self.tracker_class(instance, self.fields)
        # Expose the Tracker instance as an attribute on the model.
        setattr(instance, '_%s' % self.name, tracker)
        tracker.set_saved_fields()

    def _serialize_value(self, value):
        if type(value) is datetime.datetime:
            value = api_datetime_string(value)
        return json.dumps(value)

    def patch_save(self, instance):
        original_save = instance.save

        def save(**kwargs):
            # There are some cases where we do not want to record that a change
            # has occured, when it is not the result of a user operation.
            record_history = kwargs.pop('record_history', True)
            setattr(instance, '_record_history', record_history)

            # We only want to track changes to fields of already created models.
            if instance.pk is None or record_history is False:
                return original_save(**kwargs)

            tracker = getattr(instance, '_%s' % self.name)
            for field_name in self.fields:
                if tracker.has_changed(field_name):
                    # Note: We cannot do bulk create operations because of
                    # the multi-table inheritance that comes with polymorphism.
                    FieldAlterationEvent.objects.create(
                        content_object=instance,
                        field=field_name,
                        serialized_old_value=self._serialize_value(
                            tracker.saved_data[field_name]),
                        serialized_new_value=self._serialize_value(
                            tracker.get_field_value(field_name)),
                        user=self.get_event_user(instance),
                    )

            # Update tracker in case this model is saved again
            self.initialize_tracker(instance)
            return original_save(**kwargs)

        instance.save = save

    def get_event_user(self, instance):
        try:
            user = self.thread.request.user
        except AttributeError:
            if self._user_field is None:
                raise Exception(
                    "The user cannot be inferred from the request and the "
                    "`user_field` was not provided to the tracker.  Make sure "
                    "that the `ModelHistoryMiddleware` is installed and/or the "
                    "`user_field` is defined on initialization."
                )
            # NOTE: When using fields like `created_by` or `updated_by` that
            # may be NULL, this can cause an error if these fields are NULL
            # because the Event requires a user.  However, we really only have
            # to worry about this in tests, because all of our model operations
            # will be funneled through a request which will have the user
            # attached to it (assuming the user is logged in).
            assert hasattr(instance, self._user_field), \
                "Invalid user field %s provided." % self._user_field
            return getattr(instance, self._user_field)
        else:
            if not user.is_authenticated:
                raise Exception(
                    "User should be authenticated to perform read/write "
                    "operations!"
                )
            return user


def _get_field_events(self, field):
    return FieldAlterationEvent.objects.get_for_model_and_field(self, field)
