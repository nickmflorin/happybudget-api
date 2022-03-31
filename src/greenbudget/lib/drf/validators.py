from rest_framework import serializers, validators
from rest_framework.validators import qs_filter

from greenbudget.lib.utils import ensure_iterable, humanize_list
from greenbudget.app import exceptions


class ValidatorAttrs:
    def __init__(self):
        self._serializer = {}
        self._model = {}
        self._context = {}
        self._all = {}

    @property
    def serializer(self):
        return self._serializer

    @property
    def model(self):
        return self._model

    @property
    def context(self):
        return self._context

    @property
    def all(self):
        return self._all

    def add(self, designation, k, v):
        getattr(self, designation)[k] = v
        self._all[k] = v


class UniqueTogetherValidator(serializers.UniqueTogetherValidator):
    """
    An extension of :obj:`rest_framework.serializers.UniqueTogetherValidator`
    that solves the problem related to fields that we may need to include in
    the uniqueness check but are not defined on the serializer.

    The traditional :obj:`rest_framework.serializers.UniqueTogetherValidator`
    is used only for checking if fields defined on the serializer form a unique
    set in the model queryset.  This is used when updating or creating instances
    and the fields that form the unique set are supplied in the request.

    This isn't always the desired case however, as there are cases where we want
    to use this logic for fields that are defined in the serializer context:

    >>> class View(views.GenericView):
    >>>     def get_serializer_context(self):
    >>>         return {"user": self.request.user}

    or fields that are not on the serializer but are provided in the serializer
    save:

    >>> class View(views.GenericView):
    >>>     def perform_create(self, serializer):
    >>>         serializer.save(created_by=self.request.user)

    In both of these cases, this class allows those fields to be defined as
    `context_fields` and `model_fields` respectively.
    """
    message = "The model is not unique."

    def __init__(self, queryset, fields=None, message=None, **kwargs):
        self.context_fields = ensure_iterable(kwargs.pop('context_fields', None))
        self.model_fields = ensure_iterable(kwargs.pop('model_fields', None))
        self.exception_fields = kwargs.pop('exception_fields', None)
        super().__init__(queryset, fields or (), message=message)

    def __call__(self, data, serializer):
        attrs = ValidatorAttrs()

        for k, v in data.items():
            if k in serializer.fields:
                if k in self.fields:
                    source = serializer.fields[k].source
                    attrs.add("serializer", source, v)
            elif k in self.model_fields:
                attrs.add("model", k, v)

        for field in self.context_fields:
            assert isinstance(field, (tuple, str)), \
                "Context field must either be a string field or a tuple that " \
                "defines the field and the method to obtain the value from " \
                "the context."
            if isinstance(field, str):
                # When the instance is being created, it is more likely than not
                # that the values are already in the set of attributes provided
                # to the method - in which case, we do not want to override them.
                # pylint: disable=unsupported-membership-test
                if field not in attrs.context:
                    attrs.add("context", field, serializer.context[field])
            else:
                assert len(field) == 2 and isinstance(field[0], str) \
                    and hasattr(field[1], '__call__'), \
                    "When defined as a tuple, the context field must be " \
                    "defined as (field, callback)."
                # pylint: disable=unsupported-membership-test
                if field[0] not in attrs.context:
                    attrs.add("context", field[0], field[1](serializer.context))

        self.enforce_required_fields(attrs.serializer, serializer)
        qs = self.filter_queryset(attrs.all, self.queryset)
        qs = self.exclude_current_instance(qs, serializer.instance)

        # Ignore validation if any field is None
        checked_values = [
            v for k, v in data.items()
            if k in attrs.all
        ]
        if None not in checked_values and validators.qs_exists(qs):
            # Note: In the case that there are fields in the context or not
            # on the serializer that cause the uniqueness check to fail, it is
            # a little misleading to return a response listing these fields as
            # not being unique - as they are not provided in the request data.
            # In this case, we should be explicitly defining the error message
            # via the `message` attribute.
            message = self.message
            # The fields on the validator may not be present if they were
            # context related fields only.
            if self.fields and message is None:
                message = (
                    f"The field(s) {humanize_list(self.fields)} do not form a "
                    "unique set."
                )
            raise exceptions.ValidationError(
                message, field=self.exception_fields, code='unique')

    def filter_queryset(self, attrs, queryset):
        return qs_filter(queryset, **attrs)

    def exclude_current_instance(self, queryset, instance):
        if instance is not None:
            return queryset.exclude(pk=instance.pk)
        return queryset
