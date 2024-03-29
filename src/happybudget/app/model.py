import collections
import copy
import logging
import threading

import django
from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.db import models, IntegrityError, router

from happybudget.conf import Environments
from happybudget.lib.utils import (
    ensure_iterable, humanize_list, DynamicArgumentException)

from happybudget.app import constants, signals, query


logger = logging.getLogger('happybudget')


class PreSaveValidator:
    def __init__(self, check, message):
        self._message = message
        self._check = check

    def __call__(self, instance):
        if not self._check(instance):
            raise IntegrityError(self._message)


class model_is_deleting(signals.disable):
    """
    Context manager that manages the deleting state of a model instance while
    in the process of being deleted, and optionally suppresses signal behavior
    during the delete process if told to do so.

    Context:
    -------
    Many of the signals in this application perform certain behavior when
    a model is about to be deleted.  This behavior usually performs actions
    on a model instance that is related to the instance being deleted via a
    relational field.  However, many of these relationships define CASCADE
    deletes - which means that when one instance is deleted, the other one will
    be as well.

    If instance B is being deleted via a CASCADE delete due to instance A
    being deleted, we do not want to perform logic in the pre_delete signal
    for instance B that updates instance A (because it is also being deleted).

    Unfortunately, there is no way to tell in a signal whether or not the delete
    is happening due to a CASCADE delete or a direct deletion of the model
    instance itself.  For this reason, we expose flags on certain models that
    indicate whether or not the model is in the process of being deleted from
    a direct delete of the model instance.

    This context manager manages the flagging of the model being deleted via a
    direct delete such that signal receivers for relational models that are
    being CASCADE deleted understand that they are not being deleted directly,
    but rather as a CASCADE action from a related field.

    Parameters:
    ----------
    instance: :obj:`django.db.models.Model`
        The model instance that is being deleted.

    field_name: :obj:`str` (optional)
        The field name that is used on the model instance to indicate deleting
        state.

        Default: "is_deleting"

    disable_signals: :obj:`list` or :obj:`tuple` or :obj:`bool` (optional)
        If it is desired that signals are suppressed inside the delete context,
        this argument can be supplied as a boolean or an iterable of signals
        to suppress.

        - If provided as `True`, all signals will be suppressed inside the
          context.
        - If provided as an iterable, the signals identified inside the iterable
          will be suppressed inside the context.
        - If not provided, signals will not be suppressed inside the context.

        Default: None
    """

    def __init__(self, instance, **kwargs):
        self._instance = instance
        self._field_name = kwargs.pop('field_name', 'is_deleting')

        self._disable_signals = False
        # If `disable_signals` is provided as an iterable of signals,
        # initialize the disable context manager with those signals. Otherwise,
        # initialize the disable context manager with no signals.
        disable_signals = kwargs.pop('disable_signals', None)
        if disable_signals and not isinstance(disable_signals, bool):
            super().__init__(signals=disable_signals)
            self._disable_signals = True
        elif disable_signals is not None:
            assert isinstance(disable_signals, bool), \
                "The `disable_signals` parameter must either be an iterable " \
                "of signals or a boolean."
            self._disable_signals = disable_signals

        # If the model does not have the field that is used to indicate deleting
        # state, flag the context manager as not having valid context so that
        # entering and exiting the context manager does not update the field
        # indicating deleting state on the model instance.
        self._valid_context = True
        try:
            self._instance._meta.get_field(self._field_name)
        except FieldDoesNotExist:
            self._valid_context = False

    def __enter__(self):
        # Only enter the context for disabling the signals if the context
        # manager was instructed to perform signal suppression on initialization.
        if self._disable_signals:
            super().__enter__()
        if self._valid_context:
            setattr(self._instance, self._field_name, True)
            self._instance.save(update_fields=[self._field_name])
        return self

    def __exit__(self, *exc):
        # Only enter the context for disabling the signals if the context
        # manager was instructed to perform signal suppression on initialization.
        if self._disable_signals:
            super().__exit__()
        if self._valid_context:
            # It is often the case that the model will already be deleted by
            # the time the context exits, in which case it will not have a PK.
            if self._instance.pk is not None \
                    and getattr(self._instance, self._field_name) is True:
                setattr(self._instance, self._field_name, False)
                self._instance.save(update_fields=[self._field_name])
        return False


FieldChange = collections.namedtuple(
    'FieldChange', ['field', 'value', 'previous_value', 'field_instance'])


class FieldChanges(collections.abc.Sequence):
    """
    An iterable that contains the :obj:`FieldChange` instances associated with
    a model instance.
    """

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


class ModelException(DynamicArgumentException):
    formatters = {
        'model': lambda m: m if isinstance(m, type) else m.__class__
    }


class CallableParameterException(Exception):
    def __init__(self, param):
        self._param = param

    def __str__(self):
        return (
            "Parameter %s must either be an iterable, a single field "
            " or a callable taking the application settings as it's first and "
            "only argument." % self._param
        )


class FieldDoesNotExistError(ModelException):
    default_message = "Field {field} does not exist on model {model}."


class FieldCannotBeTrackedError(ModelException):
    default_message = "Field {field} cannot be tracked for model {model}."


class FieldNotTrackedError(ModelException):
    default_message = "Field {field} is not tracked for model {model}."


DISALLOWED_ATTRIBUTES = [('editable', False), ('primary_key', True)]
DISALLOWED_FIELDS = [models.fields.AutoField, models.ManyToManyField]
FIELDS_NOT_STORED_IN_MODEL_MEMORY = [models.ForeignKey, models.OneToOneField]


def field_tracking_is_supported(field):
    """
    Returns whether or not the provided field is supported for field tracking.
    """
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


class model:
    """
    A common decorator for all of our application's :obj:`django.db.models.Model`
    instances.  All :obj:`django.db.models.Model` instances that have connected
    signals should be decorated with this class.

    This class decorator provides the following implementations:

    (1) Signal Processing Behavior
        Connection to and communication with central application signals are
        managed for model instances that are decorated with this class.

    (2) Field Tracking Behavior
        Model classes decorated with this decorator can access tracking
        information about how fields on a given instance have changed since the
        last time the instance was saved.

    (3) Deletion Context
        Model classes that are decorated with this decorator can automatically
        indicate deleting states when the model is in the process of being
        deleted.

    (4) Deleting Signal Context
        Model classes that are decorated with this decorator will automatically
        use a custom :obj:`Collector` that will allow keyword arguments provided
        to the `.delete()` method to propogate to delete related signals.

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
    MIDDLEWARE_NAME = 'happybudget.app.middleware.ModelRequestMiddleware'

    def __init__(self, **kwargs):
        self._type = kwargs.pop('type', None)

        # Flags that can be used to disable post save signals on a save-by-save
        # basis.
        self._flags = ensure_iterable(
            kwargs.get('flags', [])) + ['track_changes']

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
                    except TypeError as e:
                        raise CallableParameterException('track_fields') from e
                self._track_fields = set([
                    f for f in ensure_iterable(track_fields)
                    if f not in self._exclude_fields
                ])
        else:
            self._track_all_fields = True

    def type(self, cls):
        # pragma: no cover
        if self._type is None:
            raise ModelException(model=cls, message=(
                "The model decorator for {model} must include the `type` "
                "parameter."
            ))
        return self._type

    def get_field_instance(self, cls, field_name):
        try:
            return cls._meta.get_field(field_name)
        except django.core.exceptions.FieldDoesNotExist as e:
            # pragma: no cover
            raise FieldDoesNotExistError(field_name, cls) from e

    def validate_field(self, cls, field):
        field_instance = self.get_field_instance(cls, field)
        # pragma: no cover
        if not field_tracking_is_supported(field_instance):
            raise FieldCannotBeTrackedError(field=field, model=cls)

    def get_supported_tracking_fields(self, cls):
        """
        Returns the names of the :obj:`django.db.models.Field` instances on the
        provide :obj:`django.db.model` class that are capable of being tracked
        and not explicitly excluded.
        """
        trackable_fields = []
        unsupported_fields = []
        for field_obj in [
            f for f in cls._meta.fields
            if f.name not in self._exclude_fields
        ]:
            if field_tracking_is_supported(field_obj):
                trackable_fields.append(field_obj.name)
            else:
                unsupported_fields.append(field_obj.name)
        if unsupported_fields:
            unsupported = humanize_list(unsupported_fields)
            logger.debug(
                f"Field(s) {unsupported} for model {cls.__name__} cannot be "
                "tracked as they are not supported."
            )
        return trackable_fields

    def tracked_fields(self, cls):
        """
        Returns either the names of the :obj:`django.db.models.Field` instances
        on the provide :obj:`django.db.model` class that are capable of being
        tracked in the case that `track_all_fields` is `True` otherwise returns
        the fields explicitly included via the `track_fields` parameter.
        """
        if self._track_all_fields:
            return self.get_supported_tracking_fields(cls)
        else:
            for field in self._track_fields:
                if field not in self._exclude_fields:
                    self.validate_field(cls, field)
            return copy.deepcopy(self._track_fields)

    def __call__(self, cls):
        cls.type = self.type(cls)

        if hasattr(cls, '__decorated_for_signals__'):
            raise ModelException(model=cls, message=(
                "Multi-table inheritance of %s not supported, base class "
                "{model} has parent that is also decorated with %s."
                % (self.__class__.__name__, self.__class__.__name__)  # noqa
            ))

        # Contains a local copy of the previous values of the fields.
        cls.__data = {}

        # The fields that are being tracked.
        cls.__tracked_fields = self.tracked_fields(cls)

        def raise_if_field_not_tracked(instance, field):
            self.validate_field(cls, field)
            # pragma: no cover
            if field not in instance.__tracked_fields:
                raise FieldNotTrackedError(field=field, model=instance)

        def was_just_added(instance):
            return getattr(instance, '__just_added', False)

        def previous_value(instance, field):
            instance.raise_if_field_not_tracked(field)
            return instance.__data[field]

        def get_last_saved_data(instance):
            return instance.__data

        def has_changes(instance):
            """
            Returns whether or not the current instance has changed since it's
            last save.
            """
            return len(instance.changed_fields) != 0

        def field_has_changed(instance, k):
            """
            Returns whether or not the provided field has changed on the instance
            since the last time the instance was saved.
            """
            if field_stored_in_local_memory(k):
                return previous_value(instance, k) != getattr(instance, k)
            return previous_value(instance, k) != getattr(instance, '%s_id' % k)

        def fields_have_changed(instance, *fields):
            """
            Returns whether or not any of the provided fields on the instance
            have changed since the last time the instance was saved.
            """
            return any([f in instance.changed_fields for f in fields])

        @property
        def changed_fields(instance):
            """
            Returns a mapping of field names to :obj:`FieldChange` instances
            for the fields on the instance that have changed since the last time
            the instance was saved.
            """
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
            """
            Returns whether or not the lookup of the provided field attribute on
            the model instance will use a potentially cached value.  Only
            applicable for certain relational fields.
            """
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

        def deleting(instance, **kwargs):
            """
            Returns a context manager that will flag the instance as being in
            the midst of the deleting process and optionally suppress signals
            while in the context.
            """
            deleting_field_name = getattr(
                instance, 'deleting_field_name', 'is_deleting')
            kwargs.setdefault('field_name', deleting_field_name)
            return model_is_deleting(instance, **kwargs)

        def delete(instance, *args, using=None, keep_parents=False, **kwargs):
            """
            Overrides the :obj:`django.db.models.Model` delete behavior in
            order to implement the following custom behavior:

            (1) Performing the Delete Inside of Context
                It is important the the delete be performed inside of the
                :obj:`model_is_deleting` context such that the deleting state
                of the instance is stored on the model.

                This has (2) implications:

                (1) The `delete` method can be provided with a `disable_signals`
                    argument that can be used to disable signals while the
                    delete is performed.

                (2) Inside the context of the `delete` method, if the instance
                    has a field that is used to indicate deleting state that
                    field will be flagged such that signals can differentiate
                    between delete behavior from CASCADE deletes and non-CASCADE
                    deletes.

            (2) Usage of Custom :obj:`Collector` Class
                It is important that the delete use the custom :obj:`Collector`
                class so that keyword arguments provided to the delete
                propogate through to the appropriate delete-related signals.
            """
            deleting_kwargs = {
                'disable_signals': kwargs.pop('disable_signals', None)
            }
            if 'field_name' in kwargs:
                deleting_kwargs.update(field_name=kwargs.pop('field_name'))

            with instance.deleting(**deleting_kwargs):
                if instance.pk is None:
                    # Let Django's original method raise the error due to
                    # the deletion of an instance that no longer exists.
                    delete._original(instance, *args, **kwargs)
                using = using or router.db_for_write(
                    instance.__class__, instance=instance)
                collector = query.Collector(using=using)
                collector.collect([instance], keep_parents=keep_parents)
                # Pass the keyword arguments into the Collector's delete method.
                return collector.delete(**kwargs)

        def validate_before_save(instance):
            validators = getattr(instance, 'pre_save_validators', [])
            assert all([isinstance(x, PreSaveValidator) for x in validators]), \
                "Encountered invalid pre save validator.  All validators must " \
                f"be an instance of {PreSaveValidator}."
            for validator in validators:
                validator(instance)
            if validate_before_save._original is not None:
                validate_before_save._original(instance)

        def save(instance, *args, **kwargs):
            """
            Overrides the :obj:`django.db.models.Model` save behavior to
            maintain the values of the model fields just after the last save,
            such that the determination of how fields have changed since the
            last model save can be made.
            """
            track_changes = kwargs.pop('track_changes', True)

            setattr(instance, '__just_added', False)
            if instance.pk is None:
                setattr(instance, '__just_added', True)

            save._original(instance, *args, **kwargs)

            dispatch_changes = []
            if instance.id is not None and track_changes is not False:
                for k in instance.__tracked_fields:
                    if instance.field_has_changed(k):
                        change = FieldChange(
                            field=k,
                            previous_value=instance.previous_value(k),
                            value=getattr(instance, k),
                            field_instance=self.get_field_instance(cls, k)
                        )
                        dispatch_changes.append(change)
                        self.send_with_user(
                            signal=signals.field_changed,
                            instance=instance,
                            signal_kwargs={'change': change}
                        )
                # Dispatch signals for the changed fields we are tracking.
                if dispatch_changes:
                    self.send_with_user(
                        signal=signals.fields_changed,
                        instance=instance,
                        signal_kwargs={
                            'changes': FieldChanges(dispatch_changes)}
                    )
            # Update the __data property on the model instance to reflect the
            # field values as they were for the last model save.
            store(instance)

        def _post_init(sender, instance, **kwargs):
            store(instance)

        def _pre_save(sender, instance, **kwargs):
            instance.validate_before_save()

        def _pre_delete(instance, **kwargs):
            self.send_with_user(
                signal=signals.pre_delete_by_user,
                instance=instance,
                signal_kwargs=kwargs
            )

        def _post_save(instance, **kwargs):
            signal = signals.post_create_by_user if kwargs['created'] \
                else signals.post_update_by_user
            self.send_with_user(signal, instance, signal_kwargs=kwargs)

        models.signals.post_init.connect(_post_init, sender=cls, weak=False)
        models.signals.post_save.connect(_post_save, sender=cls, weak=False)
        models.signals.pre_save.connect(_pre_save, sender=cls, weak=False)
        models.signals.pre_delete.connect(_pre_delete, sender=cls, weak=False)

        # Expose helper methods on the model class.
        cls.get_last_saved_data = get_last_saved_data
        cls.changed_fields = changed_fields
        cls.was_just_added = was_just_added
        cls.fields_have_changed = fields_have_changed
        cls.field_has_changed = field_has_changed
        cls.previous_value = previous_value
        cls.has_changes = has_changes
        cls.raise_if_field_not_tracked = raise_if_field_not_tracked
        cls.deleting = deleting

        # Expose the :obj:`ActionName`` class on the model class for utility
        # purposes.
        setattr(cls, 'actions', constants.ActionName)

        # Replace the model pre-save validation method with the overridden one,
        # but keep track of the original pre-save validation method so it can
        # be reapplied.
        validate_before_save._original = getattr(
            cls, 'validate_before_save', None)
        cls.validate_before_save = validate_before_save

        # Replace the model save method with the overridden one, but keep track
        # of the original save method so it can be reapplied.
        save._original = cls.save
        cls.save = save

        # Replace the model delete method with the overridden one, but keep track
        # of the original delete method so it can be reapplied.
        delete._original = cls.delete
        cls.delete = delete

        # Track that the model was decorated with this class for purposes of
        # ensuring that this decorator is not being used on a parent model
        # class.
        setattr(cls, '__decorated_for_signals__', self)
        return cls

    def send_with_user(self, signal, instance, signal_kwargs):
        for attr in [k for k in ['sender', 'signal'] if k in signal_kwargs]:
            del signal_kwargs[attr]

        force_ignore_signal_user = signal_kwargs.pop(
            'force_ignore_signal_user', False)

        # If we are intentially ignoring the user associated with the change,
        # do not include even if the user associated with the changes is
        # accessible on the thread.
        user = None
        if not force_ignore_signal_user:
            # The user may be None if the change is being performed outside of a
            # request context.
            user = self.get_user(instance, **signal_kwargs)
        signal_kwargs.update(
            sender=type(instance),
            instance=instance,
            user=user
        )
        signal.send(**signal_kwargs)

    def get_user(self, instance, **kwargs):
        # Allow the user to either be set directly on the thread or via the
        # request.  There are cases (like management commands) or tests where we
        # do not have access to the request, but can set the user on the thread
        # explicitly.
        request = getattr(self.thread, 'request', None)
        if request is not None:
            user = request.user
        else:
            user = getattr(self.thread, 'user', None)

        if user is None:
            # Ignore warnings if the user cannot be inferred from the model
            # save or delete if this flag is set.
            ignore_signal_user = kwargs.pop('ignore_signal_user', False)
            if self.MIDDLEWARE_NAME not in settings.MIDDLEWARE:
                logger.warning(
                    "The user cannot be inferred for the model change because "
                    "the appropriate middleware is not installed."
                )
            # There are cases where we are performing actions on a model and the
            # :obj:`User` is simply not applicable.  In those cases, do not
            # issue a warning.
            elif settings.ENVIRONMENT != Environments.TEST \
                    and not ignore_signal_user:
                logger.warning(
                    "The user cannot be inferred from the model change for "
                    f"model {instance.__class__}."
                )
        elif not user.is_fully_authenticated:
            # There are cases in tests where the user inferred from the
            # relevant MIDDLEWARE may not be authenticated.  We need to allow
            # this, as this often happens when creating objects from factories.
            # In this case, the user related signals will not fire - but we do
            # not want to throw a hard error.
            if settings.ENVIRONMENT != Environments.TEST:
                raise Exception(
                    f"The user editing the model {self._type} should be fully "
                    "authenticated!"
                )
            return None
        return user
