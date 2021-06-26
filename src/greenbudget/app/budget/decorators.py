from copy import deepcopy
from dataclasses import dataclass
import functools
import inspect
from typing import Any

from django.db import models
from rest_framework import decorators, response, status

from .bulk_serializers import (
    create_bulk_create_serializer,
    create_bulk_update_serializer,
    create_bulk_delete_serializer
)


@dataclass
class ActionContext:
    instance: type
    view: object
    request: Any


@dataclass
class BulkAction:
    url_path: str
    child_cls: type
    child_serializer_cls: type
    perform_create: Any = None
    perform_update: Any = None
    perform_destroy: Any = None
    filter_qs: Any = None
    child_context: Any = None
    post_save: Any = None


class bulk_action:
    def __init__(self, action, base_cls, base_serializer_cls=None,
            perform_save=None, **kwargs):
        self._action = action
        self._base_cls = base_cls
        self._base_serializer_cls = base_serializer_cls
        self._perform_save = perform_save
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
    def base_serializer_cls(self):
        if self._base_serializer_cls is None:
            if getattr(self.context.view, 'serializer_class', None) is not None:
                return getattr(self.context.view, 'serializer_class')
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
        if self._action.child_context is None:
            return {}
        elif isinstance(self._action.child_context, dict):
            return self._action.child_context
        else:
            return self._evaluate_action_callback('child_context')

    def perform_save(self, serializer):
        if self._perform_save is not None:
            assert hasattr(self._perform_save, '__call__'), \
                "The overridden save method must be a function with call " \
                "signatures."
            return self._perform_save(serializer, self.context)
        return serializer.save()

    def post_save(self, data):
        if self._action.post_save is not None:
            assert hasattr(self._action.post_save, '__call__'), \
                "The overridden post-save method must be a function with " \
                "call signatures."
            self._action.post_save(data, self.context)

    def decorated(self, view, request):
        instance = view.get_object()
        self.context = ActionContext(instance=instance, view=view, request=request)  # noqa

        serializer_cls = self.get_serializer_class()
        serializer = serializer_cls(
            instance=instance,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        data = self.perform_save(serializer)
        self.post_save(data)
        return data


class bulk_update_action(bulk_action):
    def __init__(self, action, **kwargs):
        kwargs.setdefault('perform_save', action.perform_update)
        super().__init__(action, **kwargs)

    @property
    def filter_qs(self):
        if self._action.filter_qs is None:
            return models.Q()
        if not isinstance(self._action.filter_qs, models.Q):
            return self._evaluate_action_callback('filter_qs')
        return self._action.filter_qs

    def get_serializer_class(self):
        return create_bulk_update_serializer(
            base_cls=self.base_cls,
            child_cls=self.child_cls,
            child_serializer_cls=self.child_serializer_cls,
            filter_qs=self.filter_qs,
            child_context=self.child_context
        )

    def decorated(self, view, request):
        updated_instance = super().decorated(view, request)
        return response.Response(
            self.base_serializer_cls(updated_instance).data,
            status=status.HTTP_200_OK
        )


class bulk_create_action(bulk_action):
    def __init__(self, action, **kwargs):
        kwargs.setdefault('perform_save', action.perform_create)
        super().__init__(action, **kwargs)

    def get_serializer_class(self):
        return create_bulk_create_serializer(
            base_cls=self.base_cls,
            child_cls=self.child_cls,
            child_serializer_cls=self.child_serializer_cls,
            child_context=self.child_context
        )

    def decorated(self, view, request):
        children = super().decorated(view, request)
        return response.Response(
            {'data': self.child_serializer_cls(children, many=True).data},
            status=status.HTTP_201_CREATED
        )


class bulk_delete_action(bulk_action):
    def __init__(self, action, **kwargs):
        kwargs.setdefault('perform_destroy', action.perform_destroy)
        super().__init__(action, **kwargs)

    def get_serializer_class(self):
        return create_bulk_delete_serializer(
            base_cls=self.base_cls,
            child_cls=self.child_cls
        )

    def decorated(self, view, request):
        updated_instance = super().decorated(view, request)
        return response.Response(
            self.base_serializer_cls(updated_instance).data,
            status=status.HTTP_200_OK
        )


class bulk_registration:
    def __init__(self, base_cls, base_serializer_cls=None, actions=None,
            **kwargs):
        self._base_cls = base_cls
        self._base_serializer_cls = base_serializer_cls
        self._actions = []

        actions = actions or []
        for original_action in actions:
            action = deepcopy(original_action)
            for k, v in kwargs.items():
                if getattr(action, k) is None and v is not None:
                    setattr(action, k, v)
            self._actions.append(action)

    def __call__(self, cls):
        for action in self._actions:
            self._register_action(action, cls)
        return cls

    def _register_action(self, action, cls):
        url_path = action.url_path
        if '{action_name}' in action.url_path:
            url_path = action.url_path.format(action_name=self.action_name)

        method_name = url_path.replace('-', '_')

        @self.decorate(
            action=action,
            base_cls=self._base_cls,
            base_serializer_cls=self._base_serializer_cls,
            url_path=url_path
        )
        @decorators.action(detail=True, methods=["PATCH"], url_path=url_path)
        def func(*args, **kwargs):
            pass

        func.__name__ = method_name
        # This is part of the underlying mechanics of DRF's @action
        # decorator.  Without this, we will get 404s because DRF will not
        # be able to find the appropriate function name.
        func.mapping['patch'] = method_name
        setattr(cls, method_name, func)


class register_bulk_updating(bulk_registration):
    action_name = "update"
    exclude_params = ('')

    def decorate(self, action, **kwargs):
        return bulk_update_action(action, **kwargs)


class register_bulk_creating(bulk_registration):
    action_name = "create"

    def decorate(self, action, **kwargs):
        return bulk_create_action(action, **kwargs)


class register_bulk_deleting(bulk_registration):
    action_name = "delete"

    def decorate(self, action, **kwargs):
        return bulk_delete_action(action, **kwargs)


class register_all_bulk_operations(bulk_registration):
    def __init__(self, base_cls, actions=None, **kwargs):
        super().__init__(base_cls, actions=actions)
        self._register_bulk_updating = register_bulk_updating(
            base_cls, actions=actions, **kwargs)
        self._register_bulk_creating = register_bulk_creating(
            base_cls, actions=actions, **kwargs)
        self._register_bulk_deleting = register_bulk_deleting(
            base_cls, actions=actions, **kwargs)

    def __call__(self, cls):
        self._register_bulk_updating(cls)
        self._register_bulk_creating(cls)
        self._register_bulk_deleting(cls)
        return cls
