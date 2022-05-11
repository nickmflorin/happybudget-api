import collections
from copy import deepcopy

from happybudget.app.constants import ActionName

from .bulk_decorators import (
    bulk_create_action,
    bulk_delete_action,
    bulk_update_action
)


class bulk_registration:
    """
    Abstract base class for implementations of bulk create, bulk update and bulk
    delete registration behaviors on a view.

    The implementation decorates a view class and attributes the view class with
    a series of methods that are decorated such that they expose endpoints on
    the view to handle bulk update, bulk create and/or bulk delete behavior.
    """
    def __init__(self, base_cls, get_budget, **kwargs):
        self._base_cls = base_cls
        self._get_budget = get_budget

        self._base_serializer_cls = kwargs.pop('base_serializer_cls', None)
        self._budget_serializer = kwargs.pop('budget_serializer', None)
        self._include_budget_in_response = kwargs.pop(
            'include_budget_in_response', True)

        self._actions = []

        # Keep track of what action names and entities are registered to
        # the concrete action methods so we can reverse engineer a given entity
        # or method to determine if the current view's action is associated with
        # the given entity or method.
        self._action_name_lookup = collections.defaultdict(list)
        self._action_entity_lookup = collections.defaultdict(list)

        actions = kwargs.pop('actions', [])
        for original_action in actions:
            action = deepcopy(original_action)
            for k, v in kwargs.items():
                if hasattr(action, k) and getattr(action, k) is None \
                        and v is not None:
                    setattr(action, k, v)
            self._actions.append(action)

    def __call__(self, cls):
        self._action_name_lookup = collections.defaultdict(list)
        self._action_entity_lookup = collections.defaultdict(list)

        for action in self._actions:
            self._register_action(action, cls)
            self._action_name_lookup[self.action_name].append(action.name(self))
            if action.entity is not None:
                self._action_entity_lookup[action.entity].append(
                    action.name(self))

        # Expose a property on the class instance that will return whether or
        # not we are using a bulk action method.
        def in_bulk_context(instance):
            return instance.action in getattr(
                instance, '__registered_bulk_actions', [])

        # Expose a property on the class instance that will return whether or
        # not the current action is of a given entity.
        def in_bulk_entity(instance, entity):
            if entity not in self._action_entity_lookup:
                raise LookupError(f'Unregistered entity {entity}.')
            return instance.action in self._action_entity_lookup[entity]

        # Expose a property on the class instance that will return whether or
        # not the current action is of a given action name/type.
        def in_bulk_action_name(instance, name):
            if name not in self._action_entity_lookup:
                raise LookupError(f'Unregistered action name {name}.')
            return instance.action in self._action_name_lookup[name]

        setattr(cls, 'in_bulk_context',
            property(lambda instance: in_bulk_context(instance)))
        setattr(cls, 'in_bulk_action_name', in_bulk_action_name)
        setattr(cls, 'in_bulk_entity', in_bulk_entity)
        return cls

    def _register_action(self, action, cls):
        # Keep track of what bulk context actions are registered for the view.
        setattr(cls, '__registered_bulk_actions',
            getattr(cls, '__registered_bulk_actions', []) + [action.name(self)])

        @self.decorate(
            action=action,
            base_cls=self._base_cls,
            base_serializer_cls=self._base_serializer_cls,
            url_path=action.url_path(self),
            get_budget=self._get_budget,
            budget_serializer=self._budget_serializer,
            include_budget_in_response=self._include_budget_in_response
        )
        def func(*args, **kwargs):
            pass

        func.__name__ = action.name(self)
        # This is part of the underlying mechanics of DRF's @action
        # decorator.  Without this, we will get 404s because DRF will not
        # be able to find the appropriate function name.
        func.mapping['patch'] = action.name(self)
        setattr(cls, action.name(self), func)


class register_bulk_updating(bulk_registration):
    """
    Registers a view with methods wrapped by
    :obj:`rest_framework.decorators.action` that create endpoints based on the
    provided configuration to support bulk update behavior of a series of
    model instances.
    """
    action_name = ActionName.UPDATE
    exclude_params = ('')

    def decorate(self, *args, **kwargs):
        return bulk_update_action(*args, **kwargs)


class register_bulk_creating(bulk_registration):
    """
    Registers a view with methods wrapped by
    :obj:`rest_framework.decorators.action` that create endpoints based on the
    provided configuration to support bulk create behavior of a series of
    model instances.
    """
    action_name = ActionName.CREATE

    def decorate(self, *args, **kwargs):
        return bulk_create_action(*args, **kwargs)


class register_bulk_deleting(bulk_registration):
    """
    Registers a view with methods wrapped by
    :obj:`rest_framework.decorators.action` that create endpoints based on the
    provided configuration to support bulk delete behavior of a series of
    model instances.
    """
    action_name = ActionName.DELETE

    def decorate(self, *args, **kwargs):
        return bulk_delete_action(*args, **kwargs)


class register_bulk_operations:
    """
    Registers a view with methods wrapped by
    :obj:`rest_framework.decorators.action` that create endpoints based on the
    provided configuration to support bulk update, bulk create and/or bulk
    delete behavior of a series of model instances.
    """
    registrations = [
        register_bulk_updating,
        register_bulk_creating,
        register_bulk_deleting
    ]

    def __init__(self, *args, **kwargs):
        self.id = kwargs.pop('id', None)
        exclude_action_names = kwargs.pop('exclude_action_names', [])
        action_names = kwargs.pop('action_names', None)

        self._registrated = []
        for registration in self.registrations:
            if registration.action_name not in exclude_action_names \
                    and (action_names is None
                        or registration.action_name in action_names):
                kws = deepcopy(kwargs)
                kws['actions'] = [
                    action for action in kwargs.get('actions', [])
                    if registration.action_name in action.action_names
                ]
                self._registrated.append(registration(*args, **kws))

    def __call__(self, cls):
        for registered in self._registrated:
            registered(cls)
        return cls
