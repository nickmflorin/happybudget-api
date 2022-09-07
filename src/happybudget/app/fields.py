from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from happybudget.lib.drf.fields import find_parent_base_serializer
from happybudget.lib.drf.serializers import LazyContext

from happybudget.app import exceptions
from .serializers import SerializerMixin


class PrimaryKeyRelatedField(
        SerializerMixin, serializers.PrimaryKeyRelatedField):
    """
    An extension of :obj:`rest_framework.serializers.PrimaryKeyRelatedField`
    that provides non-instrusive enhancements for common situations in which
    the field is used throughout the application.
    """
    def __init__(self, *args, **kwargs):
        # Note: Usage of this field alone will not guarantee that an error will
        # be raised if the request is not valid - but just exposes the methods
        # for making that determination.
        self._restricted_methods = kwargs.pop('restricted_methods', None)
        self._request_is_valid = kwargs.pop('request_is_valid', None)
        super().__init__(*args, **kwargs)

    @property
    def restricted_methods(self):
        if self._restricted_methods is not None:
            return [a.lower() for a in self._restricted_methods]
        return None

    @property
    def request_is_valid(self):
        if self._request_is_valid is not None:
            return self._request_is_valid(self.request, self.lazy_context)
        return self.restricted_methods is None \
            or self.request.method.lower() in self.restricted_methods

    def raise_request_if_invalid(self):
        if not self.request_is_valid:
            # It would be nice if we could instead just weed this out of the
            # data when the parent serializer accumulates the validated data
            # from the fields, but that would require mutating all serializers
            # using this field.
            raise exceptions.ValidationError(
                f"Field is not allowed for {self.request.method} requests."
            )

    @property
    def base_serializer(self):
        base = find_parent_base_serializer(self)
        assert isinstance(base, serializers.ModelSerializer), \
            "This related field must be used with ModelSerializer's only."
        return base

    @property
    def lazy_context(self):
        return LazyContext(self.base_serializer, ref=type(self).__name__)


class DualFilteredPrimaryKeyRelatedField(PrimaryKeyRelatedField):
    """
    An extension of :obj:`rest_framework.serializers.PrimaryKeyRelatedField`
    that allows optionally two different filters on the queryset differently
    and handles errors related to each one separately.

    This field class is not meant to be used directly, but is an abstract class.

    The two different filters are:

    (1) Base Queryset Filter (optional)

        The base queryset filter (if provided), indicates whether or not the
        object exists in the traditional manner.  Note that if the base query
        set is omitted, then the determination is made just based on whether or
        not the object exists at all.

    (2) Dynamic Queryset Filter (required)
        The dynamic queryset filter, applied on top of the extra, indicates
        whether or not the object exists in the overall queryset (the dynamic
        filter applied on top of any potential base filter), but in the case
        that it doesn't, will indicate whether or not the object is not in the
        overall queryset because it did not meet the requirements of the base
        filter (if provided) or the dynamic filter.

        This allows us to do the following: "The object must be an existing
        Apple instance, but it should also have a size larger than 10.  If
        the Apple instance does not exist, indicate that it does not exist at
        all - but if the size is less than 10, indicate that the size is not
        large enough."

        Note that there are cases where the dynamic queryset filter check
        cannot be performed via a simple queryset, but must be performed based
        on accessing attributes on the instances in the base queryset.  In this
        case, the dynamic queryset filter should be a function taking the
        instance as it's first and only argument and returning a boolean
        indicating whether or not the instance is valid.

        Note that this filter is required, because without it this field would
        superfluous as the generic
        :obj:`rest_framework.serializers.PrimaryKeyRelatedField` would accomplish
        the same thing.

    Since the base queryset filter is basically a workaround for the
    `queryset` argument to the traditional field, it cannot be provided as
    a callback.  But the dynamic queryset filter can be a callback, taking the
    serializer context as its first and only argument.
    """
    queryset_filter_name = None
    base_qs_filter_name = None
    instance_cls_name = None
    queryset_error_code = None

    default_error_messages = {
        # Should be overridden.
        'does_not_exist_dynamically': _(
            'The child {obj_name} with ID {pk_value} does not belong to the '
            'correct subset.'
        ),
    }

    def __init__(self, *args, **kwargs):
        # Will use the serializer's model attribute from Meta if not provided.
        instance_cls_name = self.instance_cls_name or 'instance_cls'
        self._instance_cls = kwargs.pop(instance_cls_name, None)

        queryset_filter_name = self.queryset_filter_name or 'qs_filter'
        if queryset_filter_name not in kwargs:
            raise ValueError(
                f"The parameter `{queryset_filter_name}` is required.")
        self._qs_filter = kwargs.pop(queryset_filter_name)

        base_qs_filter_name = self.base_qs_filter_name or 'base_qs_filter'
        self._base_qs_filter = kwargs.pop(base_qs_filter_name, None)

        # This is incredibly annoying: Django REST Framework preemtively checks
        # if the `queryset` argument is provided on __init__ in the case that
        # the field is not `read_only`, and will raise an error unless you have
        # overridden the `get_queryset` method.  The problem is that their
        # method for determining whether or not the `get_queryset` method is
        # overridden only checks the static child class - not the class that
        # the child class inherits from (which it would here).  To get around
        # this, we simply provide a dummy/invalid `queryset` argument to satisfy
        # Django REST Framework's __init__ method, but this parameter will never
        # be used because all extensions of this class will be equipped with the
        # overridden `get_queryset` method.
        if 'queryset' in kwargs:
            raise ValueError(
                "The queryset argument is not valid for this serializer field "
                "as it is not used."
            )
        super().__init__(*args, queryset='blah', **kwargs)

    @property
    def base_qs_filter(self):
        if isinstance(self._base_qs_filter, dict):
            return models.Q(**self._base_qs_filter)
        elif self._base_qs_filter is None:
            return models.Q()
        return self._base_qs_filter

    @property
    def qs_filter(self):
        qs_filter = self._qs_filter
        if hasattr(self._qs_filter, '__call__'):
            qs_filter = self._qs_filter(self.lazy_context)
        if isinstance(qs_filter, dict):
            return models.Q(**qs_filter)
        return qs_filter

    @property
    def instance_cls(self):
        if self._instance_cls is not None:
            if isinstance(self._instance_cls, type):
                instance_cls = self._instance_cls
            else:
                try:
                    instance_cls = self._instance_cls(self.lazy_context)
                except TypeError as e:
                    raise TypeError(
                        "`instance_cls` must either be a callable "
                        "taking serializer context as it's first and only "
                        "argument, or a class type."
                    ) from e
        else:
            instance_cls = self.base_serializer.Meta.model
        return instance_cls

    def get_base_queryset(self):
        return self.instance_cls.objects.filter(self.base_qs_filter)

    def get_queryset(self):
        bqs = self.get_base_queryset()
        # If the evaluated qs filter is itself another callable, this means that
        # the qs filter is in fact not a Django `models.Q()` instance but a
        # method that evaluates the validity of the instances in the queryset.
        # In this case, the validity of the instances will be validated outside
        # of the queryset filter.
        if hasattr(self.qs_filter, '__call__'):
            return bqs
        return bqs.filter(self.qs_filter)

    def dynamic_fail(self, pk):
        queryset_error_code = self.queryset_error_code \
            or 'does_not_exist_dynamically'
        self.fail(
            queryset_error_code,
            pk_value=pk,
            obj_name=getattr(
                self.instance_cls._meta,
                "verbose_name",
                "instance"
            ).lower(),
        )

    # pylint: disable=inconsistent-return-statements
    def to_internal_value(self, data):
        self.raise_request_if_invalid()

        if self.pk_field is not None:
            data = self.pk_field.to_internal_value(data)

        # First, we check if the instance exists in the overall queryset.  The
        # overall queryset will be the dynamic queryset applied on top of the
        # base queryset if the dynamic queryset was not a validation function.
        # If the dynamic queryset was a validation function, the overall
        # queryset will be just the base queryset.
        queryset = self.get_queryset()
        try:
            if isinstance(data, bool):
                raise TypeError
            instance = queryset.get(pk=data)
        except ObjectDoesNotExist:
            if not hasattr(self.qs_filter, '__call__'):
                # If the qs_filter is not a validation function, it was a
                # queryset filter, and the object did not exist in the dynamic
                # queryset applied on top of the base queryset.  This means we
                # have to determine whether or not the object did not exist in
                # the base queryset or the dynamic queryset.
                base_qs = self.get_base_queryset()
                try:
                    base_qs.get(pk=data)
                except ObjectDoesNotExist:
                    # Indicate that it does not exist in the traditional sense
                    # because it did not exist in the base queryset.
                    self.fail('does_not_exist', pk_value=data)
                else:
                    # The object existed in the base queryset, but not the
                    # dynamic queryset.
                    self.dynamic_fail(data)
            else:
                # If the qs_filter is a validation function, then the fact that
                # the object does not exist should be enough to tell us that
                # it did not exist in the traditional base queryset.
                self.fail('does_not_exist', pk_value=data)
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data).__name__)
        else:
            # If the qs_filter is not a validation function, the queryset
            # it exists in is just the base queryset - and we need to perform
            # the validation on the instance before returning.
            if (hasattr(self.qs_filter, '__call__')
                    # pylint: disable=not-callable
                    and not self.qs_filter(instance)):
                self.dynamic_fail(data)
            else:
                return instance
