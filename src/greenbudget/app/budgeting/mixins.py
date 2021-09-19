from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property


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
            return [permission() for permission in permission_classes]
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
    pass
