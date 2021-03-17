from copy import deepcopy
from functools import partialmethod
import logging
import threading

from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models

from .models import Event, FieldAlterationEvent


logger = logging.getLogger('backend')


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
        if field in self.saved_data:
            return self.previous(field) != getattr(self.instance, field)
        return False

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
                    getattr(cls, field).field, (models.CharField, models.DecimalField)):  # noqa
                raise Exception("Invalid/unsupported field %s." % field)

        # Currently, we can't perform this check because the app registry
        # is not loaded yet.  We should find a more appropriate place to apply
        # this check.
        # allowed_models = get_models_for_fk_choices(Event, "content_type")
        # if cls not in allowed_models:
        #     raise Exception(
        #         "Cannot track history of model %s because it is not yet "
        #         "supported by the Event model." % cls.__name__
        #     )

        setattr(cls, '_get_field_events', _get_field_events)
        for field_name in self.fields:
            field = getattr(cls, field_name)
            setattr(cls, 'get_%s_events' % field_name,
                partialmethod(cls._get_field_events, field=field))

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
            # We only want to track changes to fields of already created models.
            # This doesn't seem to be working properly however, because the
            # id is already being attributed to instances due to the .create()
            # method.  This most likely has to do with M2M fields - something
            # we should look into.
            if instance.pk is None:
                return original_save(**kwargs)

            tracker = getattr(instance, self.attname)

            for field_name in self.fields:
                if tracker.has_changed(field_name):
                    user = self.get_event_user(instance)

                    old_value = tracker.previous(field_name)
                    if old_value is not None:
                        old_value = "%s" % old_value

                    new_value = tracker.get_field_value(field_name)
                    if new_value is not None:
                        new_value = "%s" % new_value
                    # Note: We cannot do bulk create operations because of
                    # the multi-table inheritance that comes with polymorphism.
                    FieldAlterationEvent.objects.create(
                        content_object=instance,
                        field=field_name,
                        old_value=old_value,
                        new_value=new_value,
                        user=user,
                    )
            # Update tracker in case this model is saved again
            self._initialize_tracker(instance)
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
