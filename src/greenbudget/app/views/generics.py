from django.utils.functional import cached_property

from rest_framework import viewsets, serializers, generics

from greenbudget.lib.utils import ensure_iterable, get_nested_attribute
from greenbudget.app import permissions


def _get_attribute(view, attr):
    try:
        return get_nested_attribute(view, attr)
    except AttributeError as e:
        raise AttributeError(
            "View %s has invalid serializer class definition, "
            "serializer definition attribute %s does not exist "
            "on view." % (type(view).__name__, attr)
        ) from e


def _evaluate_view_attribute_map(view, mapping):
    for k, v in mapping.items():
        attr = k
        iterable_lookup = False
        if attr.endswith('__in'):
            attr = attr.split('__in')[0]
            iterable_lookup = True

        attr_value = _get_attribute(view, attr)
        if iterable_lookup and attr_value not in ensure_iterable(v):
            return False
        elif not iterable_lookup and attr_value != v:
            return False
    return True


class GenericView(generics.GenericAPIView):
    """
    An extension of `rest_framework.generics.GenericAPIView` that allows us
    to non intrusively and minorly manipulate the default behavior of the
    `rest_framework.generics.GenericAPIView` class for specific functionality
    used in this application.
    """

    def check_permissions(self, request):
        permission = permissions.AND(self.get_permissions())
        # pylint: disable=unexpected-keyword-arg
        permission.has_perm(request, self, raise_exception=True)

    def check_object_permissions(self, request, obj):
        permission = permissions.AND(self.get_permissions())
        # pylint: disable=unexpected-keyword-arg
        permission.has_obj_perm(request, self, obj, raise_exception=True)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(request=self.request, user=self.request.user)
        return context

    def get_permissions(self):
        """
        Overrides the default `.get_permissions()` method in order to provide
        the following (2) implementations:

        (1) Including Additional Permissions

            Typically, when you need to add a permission class to a specific
            view, you have to include the default permission classes again
            even though they should be included for every view based on the
            `DEFAULT_PERMISSION_CLASSES` setting.

            This method allows permission classes to be appended to the default
            permission classes by specifying the `extra_permission_classes`
            attribute.

        (2) Allowing Permissions to be Instantiated

            In our application, there are permissions that require configuration
            parameters on __init__, so the permission classes themselves have
            to be instantiated in the views.

            class View(viewsets.GenericViewSet):
                permission_classes = [IsAuthenticated(...options)]

            This is compared to the way that the DRF view traditionally expects
            them to be included, which is non-instantiated classes:

            class View(viewsets.GenericViewSet):
                permission_classes = [IsAuthenticated]
        """
        extra_permissions = getattr(self, 'extra_permission_classes', [])
        extra_permissions = ensure_iterable(extra_permissions)
        pm = list(self.permission_classes)[:] + [
            p for p in extra_permissions if p not in self.permission_classes]
        return permissions.instantiate_permissions(pm)

    def get_serializer_class(self):
        """
        Allows the serializer class that a given instance of the view should
        use to be defined dynamically based on a set of conditionals.

        For each element of `serializer_classes`, the element must either be
        an instance of :obj:`serializers.ModelSerializer` or an iterable of
        length 2.

        (1) Instance of `serializers.ModelSerializer`

            When evaluating the `serializer_classes`, if an instance of
            :obj:`serializers.ModelSerializer` is encountered, it will be
            returned.  This is typically used for listing the default serializer
            class as the last element in `serializer_classes` such that it is
            used when none of the previous conditionals are met.

        (2) Iterable of Length 2

            When evaluating the `serializer_classes`, if an iterable is
            encountered, the decision of whether or not to use the serialializer
            class (as the second element of the iterable) is made based on
            evaluating the first element of the conditional.

            The first element of the conditional can either be a dictionary
            mapping of properties and the required values on the view instance,
            or a callback taking the view instance as it's first and only
            argument.

        Example:
        --------
        serializer_classes = (
            ({'is_simple': True}, SimpleSerializer),
            (lambda view: view.instance_cls is BaseClass, BaseSerializer)
            ({'action': 'create'}, DetailSerializer),
            RegularSerializer
        )

        Additionally, the second element of a conditional serializer can also
        be another set of conditional serializers, which will only be evaluated
        if the former first element of the upper level conditional serializer
        is True.

        Example:
        --------
        serializer_classes = (
            ({'is_simple': True}, [
                (lambda view: view.instance_cls is BaseClass, BaseSerializer)
                ({'action': 'create'}, DetailSerializer),
            ]),
        )
        """
        valid_types = (list, tuple)

        def evaluate_serializer_conditional(conditional):
            if not isinstance(conditional, dict) \
                    and not hasattr(conditional, '__call__'):
                raise ValueError(
                    "View %s has invalid serializer class definition, "
                    "serializer definition must either be of type %s "
                    "or callable."
                    % (type(self).__name__, dict)
                )
            if isinstance(conditional, dict):
                return _evaluate_view_attribute_map(self, conditional)
            return conditional(self)

        def evaluate_serializer_classes(serializer_classes):
            for definition in serializer_classes:
                if not isinstance(definition, (list, tuple)) \
                        and not issubclass(
                            definition, serializers.ModelSerializer):
                    raise ValueError(
                        "View %s has invalid serializer class definition, "
                        "serializer definition must either be of types %s "
                        "or a valid subclass of %s."
                        % (
                            type(self).__name__,
                            ", ".join(["%s" % s for s in valid_types]),
                            serializers.ModelSerializer
                        )
                    )
                if isinstance(definition, valid_types):
                    if len(definition) != 2:
                        raise ValueError(
                            "View %s has invalid serializer class definition, "
                            "serializer definition must be of length 2 when "
                            "defined as an iterable." % type(self).__name__
                        )

                    if evaluate_serializer_conditional(definition[0]):
                        if isinstance(definition[1], valid_types):
                            return evaluate_serializer_classes(definition[1])
                        return definition[1]
                else:
                    # Including the serializer without any configuration
                    # conditional means that this is the default case (usually
                    # at the bottom of the array of serializer_classes) so it
                    # should be returned.
                    return definition
            return None

        if hasattr(self, 'serializer_classes'):
            evaluated = evaluate_serializer_classes(self.serializer_classes)
            if evaluated is not None:
                return evaluated

        serializer_cls = getattr(self, 'serializer_class', None)
        if serializer_cls is None:
            raise Exception(
                "View %s did not have a serializer class that met the "
                "conditional and does not define a serializer class "
                "statically." % type(self).__name__
            )
        return serializer_cls


class GenericViewSet(viewsets.ViewSetMixin, GenericView):
    """
    An extension of `rest_framework.viewsets.GenericViewSet` that allows us
    to non intrusively and minorly manipulate the default behavior of the
    `rest_framework.viewsets.GenericViewSet` class for specific functionality
    used in this application.
    """
    lookup_field = 'pk'

    @property
    def is_simple(self):
        return 'simple' in self.request.query_params

    @cached_property
    def instance(self):
        return self.get_object()

    @property
    def instance_cls(self):
        return type(self.instance)

    def _update_kwargs(self, serializer):
        kwargs = {}
        if isinstance(serializer, serializers.ModelSerializer):
            model_cls = serializer.Meta.model
            if hasattr(model_cls, 'updated_by'):
                kwargs.update(updated_by=self.request.user)
        return kwargs

    def update_kwargs(self, serializer):
        return self._update_kwargs(serializer)

    def create_kwargs(self, serializer):
        kwargs = self._update_kwargs(serializer)
        if isinstance(serializer, serializers.ModelSerializer):
            model_cls = serializer.Meta.model
            if hasattr(model_cls, 'created_by'):
                kwargs.update(created_by=self.request.user)
        return kwargs
