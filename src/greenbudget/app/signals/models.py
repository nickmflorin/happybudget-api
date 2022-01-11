import collections
from copy import deepcopy
import logging
import threading

import django
from django.conf import settings
from django.db import models

from greenbudget.conf import Environments
from greenbudget.lib.utils import ensure_iterable

from .signals import field_changed, fields_changed, post_create_by_user


logger = logging.getLogger('signals')


FieldChange = collections.namedtuple(
    'FieldChange', ['field', 'value', 'previous_value', 'field_instance'])


class FieldChanges(collections.abc.Sequence):
    def __init__(self, changes):
        self.changes = changes
        assert len([change.field for change in changes]) \
            == len(set([change.field for change in changes]))

    def __len__(self):
        return len(self.changes)

    def __getitem__(self, k):
        return self.changes[k]

    def __iter__(self):
        for change in self.changes:
            yield change


class ModelException(Exception):
    def __init__(self, model):
        self.model = model if isinstance(model, type) else model.__class__

    def __str__(self):
        return self.data.format(model=self.model.__name__)


class ModelFieldException(ModelException):
    def __init__(self, field, model):
        super().__init__(model)
        self._field = field

    def __str__(self):
        return self.data.format(field=self._field, model=self.model.__name__)


class CallableParameterException(Exception):
    def __init__(self, param):
        self._param = param

    def __str__(self):
        return (
            "Parameter %s must either be an iterable, a single field "
            " or a callable taking the application settings as it's first and "
            "only argument." % self._param
        )


class FieldDoesNotExistError(ModelFieldException):
    data = "Field {field} does not exist on model {model}."


class FieldCannotBeTrackedError(ModelFieldException):
    data = "Field {field} cannot be tracked for model {model}."


class FieldNotTrackedError(ModelFieldException):
    data = "Field {field} is not tracked for model {model}."


DISALLOWED_ATTRIBUTES = [('editable', False), ('primary_key', True)]
DISALLOWED_FIELDS = [models.fields.AutoField, models.ManyToManyField]
FIELDS_NOT_STORED_IN_MODEL_MEMORY = [models.ForeignKey, models.OneToOneField]


class model:
    """
    A common decorator for all of our applications :obj:`django.db.models.Model`
    instances.  All :obj:`django.db.models.Model` instances that have connected
    signals should be decorated with this class.  This class decorator provides
    signal processing behavior and field tracking behavior that is necessary
    for the application models to work together.

    There are some major caveats to it's usage:

    (1) Inheritance
        Use of this decorator on inherited models is prohibited as it will not
        work properly.

    (2) Updating
        Since the Django `save` method is not called when a model is updated,
        this will not work on update behavior to a queryset.

    (3) Foreign Key Fields

        When a model has an FK field, the field is actually represented by
        a :obj:`django.db.models.query_utils.DeferredAttribute` instance.
        The value on the FK field isn't actually loaded into memory until
        the attribute is accessed.  However, when this happens, it triggers
        a reinitialization of the model to store the temporary data.  This
        is problematic with post_init signals here, because it causes an
        infinite recursion when accessing FK fields inside of the post_init
        logic flow.

        For this reason, changes to FK fields are tracked with the previous
        value referencing only the ID of the FK model, not the model itself.
    """
    thread = threading.local()

    def __init__(self, flags=None, user_field=None, **kwargs):
        # Flags that can be used to disable post save signals on a save-by-save
        # basis.
        self._flags = ensure_iterable(flags) + ['track_changes']

        self._track_all_fields = False

        self._track_fields = set([])
        self._dispatch_fields = set([])
        self._exclude_fields = ensure_iterable(kwargs.pop('exclude_fields', []))

        if 'track_fields' in kwargs:
            track_fields = kwargs['track_fields']
            # If the `track_fields` argument is None or False, it means we do
            # not want to track fields at all.
            if track_fields in (None, False):
                self._track_fields = set([])
            # If the `track_fields` argument is simply set to True, it means we
            # want to track all supported fields.
            elif track_fields is True:
                self._track_all_fields = True
            else:
                # Track just the explicitly provided fields.
                if hasattr(track_fields, '__call__'):
                    try:
                        track_fields = track_fields(settings)
                    except TypeError:
                        raise CallableParameterException('track_fields')
                self._track_fields = set([
                    f for f in ensure_iterable(track_fields)
                    if f not in self._exclude_fields
                ])
        else:
            self._track_all_fields = True

        # A field on the model that is used to determine the user performing
        # the action when the request is not available.
        self._user_field = user_field
        self._track_user = kwargs.pop('track_user', True)

    def get_field_instance(self, cls, field_name):
        try:
            return cls._meta.get_field(field_name)
        except django.core.exceptions.FieldDoesNotExist:
            raise FieldDoesNotExistError(field_name, cls)

    def field_is_supported(self, field):
        for attr_set in DISALLOWED_ATTRIBUTES:
            if getattr(field, attr_set[0], None) is attr_set[1]:
                return False

        if type(field) in DISALLOWED_FIELDS:
            return False

        elif type(field) in (
            django.db.models.fields.DateTimeField,
            django.db.models.fields.DateField
        ):
            if field.auto_now_add is True or field.auto_now is True:
                return False
            return True
        return True

    def validate_field(self, cls, field):
        field_instance = self.get_field_instance(cls, field)
        if not self.field_is_supported(field_instance):
            raise FieldCannotBeTrackedError(field, cls)

    def tracked_fields(self, cls):
        if self._track_all_fields:
            tracked_fields = []
            unsupported_fields = []
            for field_obj in cls._meta.fields:
                if field_obj.name not in self._exclude_fields:
                    if self.field_is_supported(field_obj):
                        tracked_fields.append(field_obj.name)
                    else:
                        unsupported_fields.append(field_obj.name)

            if unsupported_fields:
                logger.debug(
                    "Field(s) {fields} for model {model} cannot be tracked as "
                    "they are not supported.".format(
                        model=cls.__name__,
                        fields=", ".join(unsupported_fields)
                    )
                )
            return tracked_fields
        else:
            for field in self._track_fields:
                if field not in self._exclude_fields:
                    self.validate_field(cls, field)
            return deepcopy(self._track_fields)

    def __call__(self, cls):
        if hasattr(cls, '__decorated_for_signals__'):
            raise Exception(
                "Multi-table inheritance of %s not supported, base class "
                "%s has parent that is also decorated with %s."
                % (self.__class__.__name__, cls.__name__, self.__class__.__name__)  # noqa
            )

        # Contains a local copy of the previous values of the fields.
        cls.__data = {}

        # The fields that are being tracked.
        cls.__tracked_fields = self.tracked_fields(cls)

        def raise_if_field_not_tracked(instance, field):
            self.validate_field(cls, field)
            if field not in instance.__tracked_fields:
                raise FieldNotTrackedError(field, instance)

        def was_just_added(instance):
            return getattr(instance, '__just_added', False)

        def previous_value(instance, field):
            instance.raise_if_field_not_tracked(field)
            return instance.__data[field]

        def get_last_saved_data(instance):
            return instance.__data

        def has_changes(instance):
            return len(instance.changed_fields) != 0

        def field_has_changed(instance, k):
            if field_stored_in_local_memory(k):
                return previous_value(instance, k) != getattr(instance, k)
            return previous_value(instance, k) != getattr(instance, '%s_id' % k)

        def fields_have_changed(instance, *fields):
            return any([f in instance.changed_fields for f in fields])

        @property
        def changed_fields(instance):
            changed = {}
            for k in instance.__tracked_fields:
                if field_has_changed(instance, k):
                    changed[k] = FieldChange(
                        field=k,
                        value=getattr(instance, k),
                        previous_value=previous_value(instance, k),
                        field_instance=self.get_field_instance(cls, k)
                    )
            return changed

        def field_stored_in_local_memory(field):
            if not isinstance(field, models.Field):
                field = self.get_field_instance(cls, field)
            return type(field) not in FIELDS_NOT_STORED_IN_MODEL_MEMORY

        def get_field_data(instance):
            """
            Retrieves the field value from the model's local memory state,
            without performing a DB query to obtain fields that represent
            model relationships.

            The model's local memory state is the data stored in the model's
            `__dict__` attribute.

            For fields like ForeignKey and OneToOneField, the full model is not
            actually stored in the model's local memory.  This is because the
            field is not populated in the model's local memory until it is
            accessed, because it requires a database query.  Instead, the
            PK of the associated field value is stored in the model's local
            memory, suffixed with `_id`.

            For instance, consider the following field:

            class Model(models.Model):
                parent = models.ForeignKey(...)

            Looking at a Model instance, we have

            model = Model.objects.first()
            model.__dict__
            >>> { parent_id: 1 }

            The full `parent` model will not be loaded into memory until we
            access `model.parent` - because it will only then perform a
            database query.
            """
            data = dict()
            for f in instance.__tracked_fields:
                # For non-Foreign Key type fields, the full field value
                # will be stored in the model memory and thus be present
                # in the model's __dict__ attribute.
                if field_stored_in_local_memory(f):
                    # Note that the field may or may not be in the local model
                    # `__dict__` attribute yet.
                    if f in instance.__dict__:
                        data[f] = getattr(instance, f)
                # For Foreign Key type fields, the full field value will
                # not be stored in the model memory.  Only the associated
                # ID will be stored.
                else:
                    # Note that the field may or may not be in the local model
                    # `__dict__` attribute yet.
                    if '%s_id' % f in instance.__dict__:
                        data[f] = getattr(instance, '%s_id' % f)
            return data

        def store(instance):
            instance.__data = get_field_data(instance)

        def save(instance, *args, **kwargs):
            """
            Overrides the :obj:`django.db.models.Model` save behavior to
            hook into the provided callbacks when fields are changed, fields
            are removed or the instance is created for the first time.
            """
            setattr(instance, '__just_added', False)
            if instance.pk is None:
                setattr(instance, '__just_added', True)

            new_instance = instance.id is None

            suppress_dispatch_fields = kwargs.pop(
                'suppress_dispatch_fields', False)
            track_changes = kwargs.pop('track_changes', True)

            save._original(instance, *args, **kwargs)

            dispatch_changes = []

            field_signal_kwargs = {
                'sender': type(instance),
                'instance': instance
            }
            if self._track_user:
                field_signal_kwargs['user'] = self.get_user(instance)

            if not new_instance and track_changes is not False:
                for k in instance.__tracked_fields:
                    if instance.field_has_changed(k):
                        change = FieldChange(
                            field=k,
                            previous_value=instance.previous_value(k),
                            value=getattr(instance, k),
                            field_instance=self.get_field_instance(cls, k)
                        )
                        dispatch_changes.append(change)
                        if not suppress_dispatch_fields:
                            field_changed.send(
                                change=change,
                                **field_signal_kwargs
                            )
                # Dispatch signals for the changed fields we are tracking.
                if dispatch_changes and not suppress_dispatch_fields:
                    fields_changed.send(
                        changes=FieldChanges(dispatch_changes),
                        **field_signal_kwargs
                    )
            store(instance)

        def _post_init(sender, instance, **kwargs):
            store(instance)

        def _post_save(sender, instance, **kwargs):
            if kwargs['created'] is True and self._track_user:
                post_create_by_user.send(
                    sender=type(instance),
                    instance=instance,
                    user=self.get_user(instance)
                )

        models.signals.post_init.connect(_post_init, sender=cls, weak=False)
        models.signals.post_save.connect(_post_save, sender=cls, weak=False)

        # Expose helper methods on the model class.
        cls.get_last_saved_data = get_last_saved_data
        cls.changed_fields = changed_fields
        cls.was_just_added = was_just_added
        cls.fields_have_changed = fields_have_changed
        cls.field_has_changed = field_has_changed
        cls.previous_value = previous_value
        cls.has_changes = has_changes
        cls.raise_if_field_not_tracked = raise_if_field_not_tracked

        # Replace the model save method with the overridden one, but keep track
        # of the original save method so it can be reapplied.
        save._original = cls.save
        cls.save = save

        # Track that the model was decorated with this class for purposes of
        # model inheritance and/or prevention of model inheritance.
        setattr(cls, '__decorated_for_signals__', self)

        return cls

    def get_user(self, instance):
        try:
            user = self.thread.request.user
        except AttributeError:
            user = None
            if self._user_field is not None:
                if not hasattr(instance, self._user_field):
                    raise FieldDoesNotExistError(self._user_field, instance)
                user = getattr(instance, self._user_field)
            if user is None:
                if 'greenbudget.app.signals.middleware.ModelSignalMiddleware' \
                        not in settings.MIDDLEWARE:
                    logger.warning(
                        "The user cannot be inferred for the model save "
                        "because the appropriate middleware is not installed."
                    )
                elif settings.ENVIRONMENT != Environments.TEST:
                    logger.warning(
                        "The user cannot be inferred from the model save.")
            return user
        else:
            if not user.is_authenticated or not user.is_verified:
                # Really, we should be authenticating the user in tests.  But
                # since we don't always do that, this is a PATCH for now.
                if settings.ENVIRONMENT != Environments.TEST:
                    raise Exception("The user should be authenticated!")
            return user
