from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property

from rest_framework import mixins
# pylint: disable=unused-import
from rest_framework.mixins import (  # noqa
    ListModelMixin, DestroyModelMixin, RetrieveModelMixin)

from happybudget.app import views


class UpdateModelMixin(mixins.UpdateModelMixin):
    def perform_update(self, serializer, **kwargs):
        return serializer.save(**self.update_kwargs(serializer), **kwargs)


class CreateModelMixin(mixins.CreateModelMixin):
    def perform_create(self, serializer, **kwargs):
        return serializer.save(**self.create_kwargs(serializer), **kwargs)


class NestedObjectViewMeta(type):
    def __new__(cls, name, bases, dct):
        klass = super().__new__(cls, name, bases, dct)
        view_name = getattr(klass, 'view_name', None)

        # This is the case where the cls is `NestedObjectMixin`.
        if len(bases) == 0:
            return klass

        def filter_queryset(instance, qs):
            nested_filter = f"filter_{view_name}_queryset"
            if hasattr(instance, nested_filter):
                return getattr(instance, nested_filter)(qs)
            return qs

        def get_queryset(instance):
            nested_queryset_cls_name = f"{view_name}_queryset_cls"
            nested_method_name = f"get_{view_name}_queryset"

            if hasattr(instance, nested_queryset_cls_name) \
                    and not hasattr(instance, nested_method_name):
                queryset_cls = getattr(instance, nested_queryset_cls_name)
                return queryset_cls.objects.all()

            assert hasattr(instance, nested_method_name), \
                f"The mixin {klass} requires that the method " \
                f"{nested_method_name} be defined."
            return getattr(instance, nested_method_name)()

        def get_object(instance):
            pms = getattr(instance, '%s_permission_classes' % view_name, [])
            permission = views.to_view_permission(pms)

            # pylint: disable=unexpected-keyword-arg
            queryset = filter_queryset(instance, get_queryset(instance))

            lookup_url_kwarg_attr = f"{view_name}_lookup_url_kwarg"
            lookup_url_kwarg = getattr(
                instance,
                lookup_url_kwarg_attr,
                getattr(instance, 'lookup_url_kwarg', None)
            )

            lookup_field_attr = f"{view_name}_lookup_field"
            lookup_field = getattr(
                instance,
                lookup_field_attr,
                getattr(instance, 'lookup_field')
            )

            lookup_url_kwarg = lookup_url_kwarg or lookup_field
            if lookup_url_kwarg not in instance.kwargs:
                raise Exception(
                    f'Expected view {instance.__class__.__name__} to be '
                    'called with a URL keyword argument named '
                    f'"{lookup_url_kwarg}". Fix your URL conf, or set the '
                    '`.lookup_field` attribute on the view correctly.'
                )

            filter_kwargs = {lookup_field: instance.kwargs[lookup_url_kwarg]}
            obj = get_object_or_404(queryset, **filter_kwargs)

            permission.has_obj_perm(
                instance.request, instance, obj, raise_exception=True)
            return obj

        def nested_object():
            @cached_property
            def _nested_object(instance):
                return getattr(instance, f'get_{view_name}_object')()

            _nested_object.__set_name__(cls, view_name)
            return _nested_object

        if view_name is not None:
            delattr(klass, 'view_name')
            setattr(klass, view_name, nested_object())
            setattr(klass, f'get_{view_name}_object', get_object)
        return klass


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

    POST /budgets/<pk>/children/
    GET /budgets/<pk>/children/

    A mixin can be created that extends :obj:`NestedObjectViewMixin` and defines
    permissioning methods and object lookup methods in regard to the parent
    :obj:`Budget` instance, instead of the detail instance associated with
    the viewset for the above endpoints.

    Example:
    -------
    >>> class BudgetNestedMixin(NestedObjectViewMixin):
    >>>     budget_permission_classes = [
    >>>         BudgetObjPermission
    >>>     ]
    >>>     view_name = "budget"
    >>>
    >>>     def get_budget_queryset(self):
    >>>         return Budget.objects.owned_by(self.request.user).all()

    In this example, a view that is responsible for handling the nested
    endpoints above will have access to a `budget` property, which returns
    the :obj:`Budget` instance the view nests off of.
    """
