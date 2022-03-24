import collections
from copy import deepcopy
from dataclasses import dataclass
import functools
import inspect
from typing import Any

from django.db import models
from rest_framework import decorators, response, status

from greenbudget.lib.drf.bulk_serializers import (
    create_bulk_create_serializer,
    create_bulk_update_serializer,
    create_bulk_delete_serializer
)
from greenbudget.app.constants import ActionName
from greenbudget.app.budget.serializers import BudgetSerializer


@dataclass
class ActionContext:
    instance: type
    view: object
    request: Any


class BaseBulkAction:
    """
    Abstract base class for the configuration of a bulk operation, whether it
    be the configuration of bulk create behavior, bulk delete beahvior or bulk
    update behavior.
    """
    def __init__(self, url_path: str, filter_qs: Any = None,
            name: Any = None, entity: Any = None):
        self._url_path = url_path
        self.filter_qs = filter_qs
        self._name = name
        self.entity = entity

    def url_path(self, registrar):
        url_path = self._url_path
        if '{action_name}' in url_path and '{entity}' in url_path:
            url_path = url_path.format(
                action_name=registrar.action_name,
                entity=self.entity
            )
        elif '{action_name}' in url_path:
            url_path = url_path.format(action_name=registrar.action_name)
        elif '{entity}' in url_path and self.entity is not None:
            url_path = url_path.format(entity=self.entity)
        return url_path

    def name(self, registrar):
        return self._name or self.url_path(registrar).replace('-', '_')


class BulkDeleteAction(BaseBulkAction):
    """
    Configuration for bulk delete behavior.
    """
    action_names = [ActionName.DELETE]

    def __init__(self, url_path: str, child_cls: type, **kwargs):
        super().__init__(
            url_path=url_path,
            filter_qs=kwargs.get('filter_qs'),
            name=kwargs.get('name'),
            entity=kwargs.get('entity')
        )
        self._init(child_cls, **kwargs)

    def _init(self, child_cls: type, **kwargs):
        self.child_cls = child_cls
        self.perform_destroy = kwargs.get('perform_destroy', None)


class BulkCreateAction(BaseBulkAction):
    """
    Configuration for bulk create behavior.
    """
    action_names = [ActionName.CREATE]

    def __init__(self, url_path, child_serializer_cls, **kwargs):
        super().__init__(
            url_path=url_path,
            filter_qs=kwargs.get('filter_qs'),
            name=kwargs.get('name'),
            entity=kwargs.get('entity')
        )
        self._init(child_serializer_cls, **kwargs)

    def _init(self, child_serializer_cls, **kwargs):
        self.child_serializer_cls = child_serializer_cls
        self.child_context = kwargs.get('child_context')
        self.perform_create = kwargs.get('perform_create', None)


class BulkUpdateAction(BaseBulkAction):
    """
    Configuration for bulk update behavior.
    """
    action_names = [ActionName.UPDATE]

    def __init__(self, url_path, child_serializer_cls, **kwargs):
        super().__init__(
            url_path=url_path,
            filter_qs=kwargs.get('filter_qs'),
            name=kwargs.get('name'),
            entity=kwargs.get('entity')
        )
        self._init(child_serializer_cls, **kwargs)

    def _init(self, child_serializer_cls, **kwargs):
        self.child_serializer_cls = child_serializer_cls
        self.child_context = kwargs.get('child_context')
        self.perform_update = kwargs.get('perform_update', None)


class BulkAction(BaseBulkAction):
    """
    Configuration for multiple bulk behaviors.
    """
    action_names = ActionName.__all__

    def __init__(self, url_path, child_cls, child_serializer_cls, **kwargs):
        super().__init__(
            url_path=url_path,
            filter_qs=kwargs.get('filter_qs'),
            name=kwargs.get('name'),
            entity=kwargs.get('entity')
        )
        BulkDeleteAction._init(self, child_cls, **kwargs)
        BulkCreateAction._init(self, child_serializer_cls, **kwargs)
        BulkUpdateAction._init(self, child_serializer_cls, **kwargs)


class bulk_action:
    """
    Abstract base class for decorators that decorate a method on the view
    for bulk update, bulk create and bulk delete implementations.

    The decorator wraps :obj:`rest_framework.decorators.action` such that an
    endpoint is registered on the view class to handle the bulk update, bulk
    create or bulk delete behavior.

    Parameters:
    ----------
    For the following parameters, we reference "callback" as a function type that
    takes the :obj:`ActionContext` for the given action as it's first and only
    argument and returns the relevant value.

    action: :obj:`BaseBulkAction`
        The :obj:`BaseBulkAction` configuration for the bulk implementation that
        the decorator is implementing.

    base_cls: :obj:`type` or "callback"
        The Django model class that the children are being updated, created or
        deleted relative to.

    get_budget: :obj:`lambda`
        A callback that takes the instance associated with the `base_cls` model
        and returns the relevant :obj:`Budget` or :obj:`Template` instance
        relevant to the specific view.

        If the `base_cls` is :obj:`Budget` or :obj:`Template`, the callback
        simply returns the identity.

    include_budget_in_response: :obj:`bool` (optional)
        Whether or not the :obj:`Budget` or :obj:`Template` should be serialized
        in the response rendered after the bulk update, bulk create or bulk
        delete operation.

        Default: True

    budget_serializer: :obj:`type` or "callback" (optional)
        Either a serializer class or a callback returning the serializer class
        that should be used to serialize the :obj:`Budget` or :obj:`Template`
        in the response in the case that `include_budget_in_response` is True.

        Default: BudgetSerializer

    Private Parameters:
    ------------------
    These parameters are exposed for purposes of usage of this class as an
    abstract base class and are not exposed to outside implementations of any
    of the extensions of this base class.

    perform_save: :obj:`lambda` (optional)
        A callback that takes the serializer as it's first argument and the
        :obj:`ActionContext` as it's second argument.  The callback can be used
        in place of the traditional `serializer.save` method in the case that
        additional parameters are required for the `serializer.save` method.

        The `perform_save` method is chosen by the individual extensions of this
        abstract base class based on the type of bulk operation being performed.

        Default: None

    **kwargs
        Additional keyword arguments that can be provided to the root
        :obj:`rest_framework.decorators.action` decorator.
    """
    def __init__(self, action, base_cls, get_budget, **kwargs):
        self._action = action
        self._base_cls = base_cls

        self._base_serializer_cls = kwargs.pop('base_serializer_cls', None)

        # Ability to override the default `serializer.save()` call.
        self._perform_save = kwargs.pop('perform_save', None)

        # A way to get the Budget or Template instance from the instance being
        # updated.  This is used to return the updated Budget/Template in the
        # response and provide the Budget/Template in the serializer context.
        # If we are bulk changing the Account(s) of a Budget/Template, then the
        # updated instance already is the Budget/Template, so we do not need
        # to include the Budget/Template in the response again.  In this case,
        # we set `include_budget_in_response` to False.
        self._get_budget = get_budget
        self._budget_serializer = kwargs.pop('budget_serializer', None)
        self._include_budget_in_response = kwargs.pop(
            'include_budget_in_response', True)

        # Additional kwargs passed directly through to Django REST Framework's
        # :obj:`rest_framework.decorators.action`.
        self._kwargs = kwargs

        self.context = None

    def __call__(self, func):
        @decorators.action(detail=True, methods=["PATCH"], **self._kwargs)
        @functools.wraps(func)
        def method(view, request, *args, **kwargs):
            return self.decorated(view, request)
        return method

    def _evaluate_callback(self, attr):
        callback = getattr(self, '_%s' % attr)
        assert hasattr(callback, '__call__'), \
            "The `%s` attribute must either be provided explicitly as a value" \
            " or a callback returning the value."
        return callback(self.context)

    def _evaluate_action_callback(self, attr):
        callback = getattr(self._action, attr)
        assert hasattr(callback, '__call__'), \
            "The `%s` attribute must either be provided explicitly as a value" \
            " or a callback returning the value."
        return callback(self.context)

    @property
    def base_cls(self):
        if inspect.isclass(self._base_cls):
            return self._base_cls
        return self._evaluate_callback('base_cls')

    @property
    def budget_serializer(self):
        if self._budget_serializer is None:
            return BudgetSerializer
        elif inspect.isclass(self._budget_serializer):
            return self._budget_serializer
        return self._evaluate_callback('budget_serializer')

    @property
    def base_serializer_cls(self):
        if self._base_serializer_cls is None:
            return self.context.view.get_serializer_class()
        elif inspect.isclass(self._base_serializer_cls):
            return self._base_serializer_cls
        return self._evaluate_callback('base_serializer_cls')

    @property
    def child_cls(self):
        if inspect.isclass(self._action.child_cls):
            return self._action.child_cls
        return self._evaluate_action_callback('child_cls')

    @property
    def child_serializer_cls(self):
        if inspect.isclass(self._action.child_serializer_cls):
            return self._action.child_serializer_cls
        return self._evaluate_action_callback('child_serializer_cls')

    @property
    def child_context(self):
        budget = self._get_budget(self.context.instance)
        default_context = {'budget': budget}
        if self._action.child_context is None:
            return default_context
        elif isinstance(self._action.child_context, dict):
            return {**self._action.child_context, **default_context}
        else:
            return {
                **self._evaluate_action_callback('child_context'),
                **default_context
            }

    def perform_save(self, serializer):
        if self._perform_save is not None:
            assert hasattr(self._perform_save, '__call__'), \
                "The overridden save method must be a function with call " \
                "signatures."
            return self._perform_save(serializer, self.context)
        return serializer.save()

    def decorated(self, view, request):
        instance = view.get_object()
        self.context = ActionContext(
            instance=instance, view=view, request=request)
        serializer_cls = self.get_serializer_class()
        serializer = serializer_cls(
            instance=instance,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        data = self.perform_save(serializer)
        return data

    def render_response(self, data, **kwargs):
        if self._include_budget_in_response is True:
            budget = self._get_budget(self.context.instance)
            budget.refresh_from_db()
            data['budget'] = self.render_serializer_data(
                self.budget_serializer,
                instance=budget,
            )
        kwargs.setdefault('status', status.HTTP_200_OK)
        return response.Response(data, **kwargs)

    def render_serializer_data(self, serializer_cls, *args, **kwargs):
        kwargs['context'] = self.context.view.get_serializer_context()
        return serializer_cls(*args, **kwargs).data


class bulk_update_action(bulk_action):
    """
    Decorates a method on the view class such that it supports bulk update
    behavior.
    """
    def __init__(self, action, *args, **kwargs):
        kwargs.setdefault('perform_save', action.perform_update)
        super().__init__(action, *args, **kwargs)

    @property
    def filter_qs(self):
        if self._action.filter_qs is None:
            return models.Q()
        if not isinstance(self._action.filter_qs, models.Q):
            return self._evaluate_action_callback('filter_qs')
        return self._action.filter_qs

    def get_serializer_class(self):
        return create_bulk_update_serializer(
            model_cls=self.base_cls,
            serializer_cls=self.child_serializer_cls,
            filter_qs=self.filter_qs,
            child_context=self.child_context
        )

    def decorated(self, view, request):
        instance, children = super().decorated(view, request)
        return self.render_response({
            'children': self.render_serializer_data(
                self.child_serializer_cls,
                children,
                many=True
            ),
            'parent': self.render_serializer_data(
                self.base_serializer_cls,
                instance=instance
            ),
        }, status=status.HTTP_200_OK)


class bulk_create_action(bulk_action):
    """
    Decorates a method on the view class such that it supports bulk create
    behavior.
    """
    def __init__(self, action, *args, **kwargs):
        kwargs.setdefault('perform_save', action.perform_create)
        super().__init__(action, *args, **kwargs)

    def get_serializer_class(self):
        return create_bulk_create_serializer(
            model_cls=self.base_cls,
            serializer_cls=self.child_serializer_cls,
            child_context=self.child_context
        )

    def decorated(self, view, request):
        instance, children = super().decorated(view, request)
        return self.render_response({
            'children': self.render_serializer_data(
                self.child_serializer_cls,
                children,
                many=True
            ),
            'parent': self.render_serializer_data(
                self.base_serializer_cls,
                instance=instance
            ),
        }, status=status.HTTP_201_CREATED)


class bulk_delete_action(bulk_action):
    """
    Decorates a method on the view class such that it supports bulk delete
    behavior.
    """
    def __init__(self, action, *args, **kwargs):
        kwargs.setdefault('perform_destroy', action.perform_destroy)
        super().__init__(action, **kwargs)

    def get_serializer_class(self):
        return create_bulk_delete_serializer(
            model_cls=self.base_cls,
            child_cls=self.child_cls
        )

    def decorated(self, view, request):
        updated_instance = super().decorated(view, request)
        return self.render_response({'parent': self.render_serializer_data(
            self.base_serializer_cls,
            instance=updated_instance
        )})


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
