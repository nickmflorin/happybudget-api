from dataclasses import dataclass
import functools
import inspect
from typing import Any

from django.db import models
from rest_framework import decorators, response, status

from greenbudget.app.serializers import (
    create_bulk_create_serializer,
    create_bulk_update_serializer,
    create_bulk_delete_serializer
)


@dataclass
class ActionContext:
    instance: type
    view: object
    request: Any


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
        # pylint: disable=import-outside-toplevel,unused-import
        from greenbudget.app.budget.serializers import BudgetSerializer

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
