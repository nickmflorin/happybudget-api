from rest_framework import serializers, validators, exceptions

from greenbudget.lib.utils import ensure_iterable, humanize_list


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
        super().__init__(queryset, fields or (), message=message)

    def __call__(self, data, serializer):
        attrs = {
            'context': {},
            'model': {},
            'serializer': {}
        }

        for k, v in data.items():
            if k in serializer.fields:
                attrs['serializer'][k] = v
            else:
                attrs['model'][k] = v

        for field in self.context_fields:
            assert isinstance(field, (tuple, str)), \
                "Context field must either be a string field or a tuple that " \
                "defines the field and the method to obtain the value from " \
                "the context."
            if isinstance(field, str):
                # When the instance is being created, it is more likely than not
                # that the values are already in the set of attributes provided
                # to the method - in which case, we do not want to override them.
                if field not in attrs:
                    attrs['context'][field] = getattr(serializer.context, field)
            else:
                assert len(field) == 2 and isinstance(field[0], str) \
                    and hasattr(field[1], '__call__'), \
                    "When defined as a tuple, the context field must be " \
                    "defined as (field, callback)."
                if field[0] not in attrs:
                    attrs['context'][field[0]] = field[1](serializer.context)

        self.enforce_required_fields(attrs['serializer'], serializer)
        qs = self.filter_queryset(data, self.queryset, serializer)
        qs = self.exclude_current_instance(data, qs, serializer.instance)

        # Ignore validation if any field is None
        checked_values = [
            v for k, v in data.items()
            if k in attrs['context'] or k in attrs['serializer']
            or k in attrs['model']
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
            if self.fields:
                message = (
                    f"The fields {humanize_list(self.fields)} do not form a "
                    "unique set."
                )
            raise exceptions.ValidationError(message, code='unique')
