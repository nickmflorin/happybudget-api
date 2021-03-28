import logging
import threading

import django
from django.db import models


logger = logging.getLogger('greenbudget')


class track_model:
    """
    Tracks field alterations and other save behaviors of a
    :obj:`django.db.models.Model`.
    NOTE:
    ----
    IMPORTANT: Since the Django `save` method is not called when a model
    is updated (i.e. Model.objects.filter().update()) - this will not work.
    Unfortunately, since the .update() method is so close to the SQL layer,
    there really isn't a way in Django to avoid this.
    """
    thread = threading.local()

    def __init__(self, **configuration):
        # The fields that are being tracked for specific cases.
        self._track_changes_to_fields = configuration.get(
            'track_changes_to_fields', [])
        self._track_removal_of_fields = configuration.get(
            'track_removal_of_fields', [])

        # Specific hooks to use for specific fields.
        self._on_field_removal_hooks = configuration.get(
            'on_field_removal_hooks', {})
        self._on_field_change_hooks = configuration.get(
            'on_field_change_hooks', {})

        # The hooks that are called when certain conditions are met.
        self._on_field_removal = configuration.get('on_field_removal', [])
        if self._on_field_removal is None:
            self._on_field_removal = []
        if type(self._on_field_removal) not in (list, tuple):
            self._on_field_removal = [self._on_field_removal]
        self._on_field_removal = [
            f for f in self._on_field_removal if f is not None]

        self._on_create = configuration.get('on_create', [])
        if self._on_create is None:
            self._on_create = []
        if type(self._on_create) not in (list, tuple):
            self._on_create = [self._on_create]
        self._on_create = [f for f in self._on_create if f is not None]

        self._on_field_change = configuration.get('on_field_change', [])
        if self._on_field_change is None:
            self._on_field_change = []
        if type(self._on_field_change) not in (list, tuple):
            self._on_field_change = [self._on_field_change]
        self._on_field_change = [
            f for f in self._on_field_change if f is not None]

        # A field on the model that is used to determine the user performing
        # the action when the request is not available.
        self._user_field = configuration.get('user_field')

        # Flags that are provided to toggle behavior on save.
        self._flags = configuration.get('flags', [])

        for field in self.provided_fields:
            if not isinstance(field, str):
                raise ValueError(
                    "Invalid Field %s - The field must be a string "
                    "corresponding to a field on the model." % field
                )

    def __call__(self, cls):
        self.validate_configuration(cls)

        # If the class has already been decorated, that means it is a class
        # that extends a model that has already been decorated.  In the future,
        # we want to be able to figure out how to allow the patched save method
        # to work with Polymorphism, but for now, we will just raise an
        # exception.
        if hasattr(cls, '__track_model_decorated__'):
            raise Exception("`track_model` does not support model inheritance.")

        # Contains a local copy of the previous values of the fields.
        cls.__data = {}

        # The fields that are being tracked.
        cls.__tracked_fields = self.provided_fields

        # The fields that are being tracked for specific cases.
        cls.__tracked_fields_for_removal = self._track_removal_of_fields
        cls.__tracked_fields_for_change = self._track_changes_to_fields

        # Specific hooks to use for specific fields.
        cls.__on_field_removal_hooks = self._on_field_removal_hooks
        cls.__on_field_change_hooks = self._on_field_change_hooks

        # The hooks that are called when certain conditions are met.
        cls.__on_field_removal = self._on_field_removal
        cls.__on_field_change = self._on_field_change
        cls.__on_create = self._on_create

        # Flags that are provided to toggle behavior on save.
        cls.__flags = self._flags

        def field_changed(instance, field):
            """
            Returns a boolean to indicate whether or not the provided field
            has changed since the last time the model was saved.
            Parameters:
            ----------
            field: :obj:`str`
                The name of the field on the model.
            """
            if field not in instance.__tracked_fields:
                raise ValueError("The field %s is not being tracked." % field)
            if instance.id is None:
                raise ValueError("The instance has not yet been saved.")
            if instance.__data[field] != getattr(instance, field):
                return True
            return False

        def previous_value(instance, field):
            """
            Returns the previous value for the provided field before the last
            save.

            Parameters:
            ----------
            field: :obj:`str`
                The name of the field on the model.
            """
            if field not in instance.__tracked_fields:
                raise ValueError("The field %s is not being tracked." % field)
            if instance.id is None:
                raise ValueError("The instance has not yet been saved.")
            return instance.__data[field]

        @property
        def changed_fields(instance):
            """
            Returns a dictionary of field names and values for the fields that
            have changed since the last save.
            """
            changed = {}
            if instance.id is not None:
                instance.__data['group'] = instance.group
                for k in instance.__tracked_fields:
                    if k in instance.__data \
                            and instance.__data[k] != getattr(instance, k):
                        changed[k] = instance.__data[k]
            return changed

        def store(instance):
            """
            Attributes the current values of the instance for each field that
            :obj:`track_model` is configured for to a local store on the model.
            This store is used at a later point in time to determine if any
            fields have changed.

            NOTE:
            ----
            There are some caveats to this, as it relates to Django, post_init
            signals and ForeignKey fields.

            When a model has an FK field, the field is actually represented by
            a :obj:`django.db.models.query_utils.DeferredAttribute` instance.
            The value on the FK field isn't actually loaded into memory until
            the attribute is accessed.  However, when this happens, it triggers
            a reinitialization of the model to store the temporary data.  This
            is problematic with post_init signals, because it causes an
            infinite recursion when accessing FK fields inside of the post_init
            logic flow.

            That is exactly what is happening here - we are accessing the FK
            fields inside of a chain of logic that is triggered on post_init,
            which causes an infinite recursion.  To get around this, we only
            track fields that are already loaded into memory (non FK fields)
            and for FK fields, we just track the ID of the associated model -
            preventing the FK instance from being loaded into memory and
            causing an infinite recursion.
            """
            instance.__data = dict()
            if instance.id:
                for f in instance.__tracked_fields:
                    # Only load the field into the store if it is already
                    # loaded into memory.
                    if f in instance.__dict__:
                        instance.__data[f] = getattr(instance, f)
                    # If the field is not already loaded into memory, it may
                    # be a FK field - so we only track the associated ID.
                    elif '%s_id' % f in instance.__dict__:
                        instance.__data[f] = getattr(instance, '%s_id' % f)

        def save(instance, *args, **kwargs):
            """
            Overrides the :obj:`django.db.models.Model` save behavior to
            hook into the provided callbacks when fields are changed, fields
            are removed or the instance is created for the first time.
            """
            new_instance = instance.id is None

            track_changes = kwargs.pop('track_changes', True)
            setattr(instance, '_track_changes', track_changes)
            save._original(instance, *args, **kwargs)

            if not new_instance and track_changes is True:
                for k in instance.__tracked_fields:
                    if instance.field_changed(k):
                        # Call either the specifically provided hook for the
                        # field or the general hook for the case when the field
                        # has changed.
                        if k in self._on_field_change_hooks:
                            self._on_field_change_hooks[k](instance, {
                                'previous_value': instance.previous_value(k),
                                'new_value': getattr(instance, k),
                                'user': self.get_user(instance),
                            })
                        elif k in self._track_changes_to_fields \
                                and self._on_field_change is not None:
                            for hook in self._on_field_change:
                                hook(instance, k, {
                                    'previous_value': instance.previous_value(k),  # noqa
                                    'new_value': getattr(instance, k),
                                    'user': self.get_user(instance),
                                })
                        # Call either the specifically provided hook for the
                        # field or the general hook for the case when the field
                        # has been removed.
                        if k in self._on_field_removal_hooks:
                            self._on_field_removal_hooks[k](instance, {
                                'previous_value': instance.previous_value(k),
                                'new_value': getattr(instance, k),
                                'user': self.get_user(instance),
                            })
                        elif k in self._track_removal_of_fields \
                                and self._on_field_removal is not None:
                            for hook in self._on_field_removal:
                                hook(instance, k, {
                                    'previous_value': instance.previous_value(k),  # noqa
                                    'new_value': getattr(instance, k),
                                    'user': self.get_user(instance),
                                })
            store(instance)

        def _post_init(sender, instance, **kwargs):
            store(instance)

        def _post_save(sender, instance, **kwargs):
            if kwargs['created'] is True and instance._track_changes is True \
                    and instance.__on_create is not None:
                user = self.get_user(instance)
                for hook in instance.__on_create:
                    hook(instance, {'user': user})

        models.signals.post_init.connect(_post_init, sender=cls, weak=False)
        models.signals.post_save.connect(_post_save, sender=cls, weak=False)

        # Expose helper methods on the model class.
        cls.changed_fields = changed_fields
        cls.field_changed = field_changed
        cls.previous_value = previous_value

        # Replace the model save method with the overridden one, but keep track
        # of the original save method so it can be reapplied.
        save._original = cls.save
        cls.save = save

        # Track that the model was decorated with this class for purposes of
        # model inheritance and/or prevention of model inheritance.
        setattr(cls, '__track_model_decorated__', self)

        return cls

    @property
    def provided_fields(self):
        return list(set(
            self._track_removal_of_fields + self._track_changes_to_fields))

    def validate_field(self, klass, field):
        try:
            klass._meta.get_field(field)
        except django.core.exceptions.FieldDoesNotExist:
            raise ValueError(
                "The field %s does not exist on the model %s."
                % (field, klass.__name__))

    def validate_configuration(self, klass):
        for field in self.provided_fields:
            self.validate_field(klass, field)
        for k, _ in self._on_field_removal_hooks.items():
            self.validate_field(klass, k)
        for k, _ in self._on_field_change_hooks.items():
            self.validate_field(klass, k)

    def get_user(self, instance):
        try:
            user = self.thread.request.user
        except AttributeError:
            if self._user_field is None:
                logger.warn(
                    "The user cannot be inferred from the request and the "
                    "`user_field` was not provided to the tracker.  Make sure "
                    "that the `ModelHistoryMiddleware` is installed and/or the "
                    "`user_field` is defined on initialization."
                )
            else:
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
