from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property

from rest_framework import mixins
from rest_framework.mixins import (  # noqa
    ListModelMixin, DestroyModelMixin, RetrieveModelMixin)


class UpdateModelMixin(mixins.UpdateModelMixin):
    def perform_update(self, serializer, **kwargs):
        return serializer.save(**self.update_kwargs(serializer), **kwargs)


class CreateModelMixin(mixins.CreateModelMixin):
    def perform_create(self, serializer, **kwargs):
        return serializer.save(**self.create_kwargs(serializer), **kwargs)


class NestedObjectViewMeta(type):
    def __new__(cls, name, bases, dct):
        klass = super().__new__(cls, name, bases, dct)

        # This is the case where the cls is `NestedObjectMixin`.
        if len(bases) == 0:
            return klass

        view_name = getattr(klass, 'view_name', None)
        if view_name is not None:
            delattr(klass, 'view_name')

            setattr(klass, 'get_%s_permissions' %
                    view_name, cls.get_permissions(klass, view_name))
            setattr(klass, 'check_%s_object_permissions' %
                    view_name, cls.check_object_permissions(klass, view_name))
            setattr(klass, 'check_%s_permissions' %
                    view_name, cls.check_permissions(klass, view_name))
            setattr(klass, view_name, cls.nested_object(klass, view_name))
        return klass

    def get_permissions(cls, view_name):
        def _get_permissions(instance):
            permission_classes = getattr(
                instance, '%s_permission_classes' % view_name, [])
            return [
                p() if isinstance(p, type) else p
                for p in permission_classes
            ]
        return _get_permissions

    def check_object_permissions(cls, view_name):
        def _check_object_permissions(instance, request, obj):
            getter = getattr(instance, 'get_%s_permissions' % view_name)
            for permission in getter():
                if not permission.has_object_permission(request, instance, obj):
                    instance.permission_denied(
                        request,
                        message=getattr(permission, 'message', None)
                    )
        return _check_object_permissions

    def check_permissions(cls, view_name):
        def _check_permissions(instance, request):
            getter = getattr(instance, 'get_%s_permissions' % view_name)
            for permission in getter():
                if not permission.has_permission(request, instance):
                    instance.permission_denied(
                        request,
                        message=getattr(permission, 'message', None)
                    )
        return _check_permissions

    def nested_object(cls, view_name):
        @cached_property
        def _nested_object(instance):
            check_object_permissions = getattr(
                instance, 'check_%s_object_permissions' % view_name)
            check_permissions = getattr(
                instance, 'check_%s_permissions' % view_name)

            lookup_field = getattr(
                instance, '%s_lookup_field' % view_name, None)
            if lookup_field is None:
                raise NotImplementedError(
                    "%s must define the @property %s."
                    % (cls.__name__, '%s_lookup_field' % view_name)
                )
            qs_getter = getattr(instance, 'get_%s_queryset' % view_name, None)
            if qs_getter is None:
                raise NotImplementedError(
                    "%s must define the method %s."
                    % (cls.__name__, 'get_%s_queryset' % view_name)
                )
            check_permissions(instance.request)
            qs = qs_getter(instance.request)
            obj = get_object_or_404(qs, **{
                lookup_field[0]: instance.kwargs[lookup_field[1]]
            })
            check_object_permissions(instance.request, obj)
            return obj

        _nested_object.__set_name__(cls, view_name)
        return _nested_object


class NestedObjectViewMixin(metaclass=NestedObjectViewMeta):
    """
    Base mixin class for a mixin that defines how a view extends off of an
    instance's detail endpoint.  Mixin classes that extend this mixin can be
    used by a view to allow traditional Django REST Framework view mechanics,
    in regard to permissioning and object lookup methods, to be performed on the
    parent instance that a series of endpoints may nest off of.

    For instance, we may have an detail endpoint for a :obj:`Budget` with the
    following behaviors:

    PATCH /budgets/<pk>/
    GET /budgets/<pk>/

    This endpoint is responsible for actions that pertain to a specific
    :obj:`Budget` instance.  However,  there may be a series of other behaviors
    that we want to branch off of this endpoint such that they are still
    associated with a single :obj:`Budget` instance:

    POST /budgets/<pk>/accounts/
    GET /budgets/<pk>/accounts/

    A mixin can be created that extends :obj:`NestedObjectViewMixin` and defines
    permissioning methods and object lookup methods in regard to the parent
    :obj:`Budget` instance, instead of the detail instance associated with
    the viewset for the above endpoints.

    Example:
    -------
    >>> class BudgetNestedMixin(NestedObjectViewMixin):
    >>>     budget_permission_classes = [
    >>>         BudgetProductPermission
    >>>     ]
    >>>     view_name = "budget"
    >>>     budget_lookup_field = ("pk", "budget_pk")
    >>>
    >>>     def get_budget_queryset(self, request):
    >>>         return Budget.objects.filter(created_by=request.user).all()

    In this example, a view that is responsible for handling the nested
    endpoints above will have access to a `budget` property, which returns
    the :obj:`Budget` instance the view nests off of.
    """
    pass
