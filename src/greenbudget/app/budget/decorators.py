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
from .serializers import BudgetSerializer


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
    def __init__(self, action, base_cls, child_context_indicator, get_budget,
            **kwargs):
        self._action = action
        self._base_cls = base_cls

        # Used to let the children serializers know that we are in a specific
        # bulk context.
        self._child_context_indicator = child_context_indicator

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
        self._budget_serializer = kwargs.pop(
            'budget_serializer', BudgetSerializer) or BudgetSerializer
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
        budget = self._get_budget(self.context.instance)
        default_context = {'budget': budget, self._child_context_indicator: True}  # noqa
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

    def render_response(self, data, status=status.HTTP_200_OK):
        if self._include_budget_in_response is True:
            budget = self._get_budget(self.context.instance)
            budget.refresh_from_db()
            data['budget'] = self._budget_serializer(budget).data
        return response.Response(data, status=status)


class bulk_update_action(bulk_action):
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
            base_cls=self.base_cls,
            child_cls=self.child_cls,
            child_serializer_cls=self.child_serializer_cls,
            filter_qs=self.filter_qs,
            child_context=self.child_context
        )

    def decorated(self, view, request):
        updated_instance = super().decorated(view, request)
        return self.render_response({
            'data': self.base_serializer_cls(updated_instance).data})


class bulk_create_action(bulk_action):
    def __init__(self, action, *args, **kwargs):
        kwargs.setdefault('perform_save', action.perform_create)
        super().__init__(action, *args, **kwargs)

    def get_serializer_class(self):
        return create_bulk_create_serializer(
            base_cls=self.base_cls,
            child_cls=self.child_cls,
            child_serializer_cls=self.child_serializer_cls,
            child_context=self.child_context
        )

    def decorated(self, view, request):
        instance, children = super().decorated(view, request)
        return self.render_response({
            'children': self.child_serializer_cls(children, many=True).data,
            'data': self.base_serializer_cls(instance).data
        }, status=status.HTTP_201_CREATED)


class bulk_delete_action(bulk_action):
    def __init__(self, action, *args, **kwargs):
        kwargs.setdefault('perform_destroy', action.perform_destroy)
        super().__init__(action, **kwargs)

    def get_serializer_class(self):
        return create_bulk_delete_serializer(
            base_cls=self.base_cls,
            child_cls=self.child_cls
        )

    def decorated(self, view, request):
        updated_instance = super().decorated(view, request)
        return self.render_response({
            'data': self.base_serializer_cls(updated_instance).data})


class bulk_registration:
    def __init__(self, base_cls, get_budget, child_context_indicator,
            base_serializer_cls=None, actions=None, budget_serializer=None,
            include_budget_in_response=True, **kwargs):
        self._base_cls = base_cls
        self._base_serializer_cls = base_serializer_cls
        self._get_budget = get_budget
        self._child_context_indicator = child_context_indicator
        self._budget_serializer = budget_serializer
        self._include_budget_in_response = include_budget_in_response

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
            url_path=url_path,
            get_budget=self._get_budget,
            child_context_indicator=self._child_context_indicator,
            budget_serializer=self._budget_serializer,
            include_budget_in_response=self._include_budget_in_response
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

    def decorate(self, *args, **kwargs):
        return bulk_update_action(*args, **kwargs)


class register_bulk_creating(bulk_registration):
    action_name = "create"

    def decorate(self, *args, **kwargs):
        return bulk_create_action(*args, **kwargs)


class register_bulk_deleting(bulk_registration):
    action_name = "delete"

    def decorate(self, *args, **kwargs):
        return bulk_delete_action(*args, **kwargs)


class register_all_bulk_operations(bulk_registration):
    registrations = [
        register_bulk_updating,
        register_bulk_creating,
        register_bulk_deleting
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._registrated = []
        for registration in self.registrations:
            self._registrated.append(registration(*args, **kwargs))

    def __call__(self, cls):
        for registered in self._registrated:
            registered(cls)
        return cls
