from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from greenbudget.lib.drf.fields import find_parent_base_serializer


class UserDateTimeFieldDefault:
    """
    Returns the default value as now in the user's timezone when used as the
    default to a :obj:`rest_framework.serializers.DateTimeField`.
    """
    requires_context = True

    def __call__(self, serializer_field):
        assert 'request' in serializer_field.context, \
            "The request must be provided in context when using this default."
        return self.context['request'].user.now_in_timezone


class UserDateFieldDefault(UserDateTimeFieldDefault):
    """
    Returns the default value as today in the user's timezone when used as the
    default to a :obj:`rest_framework.serializers.DateField`.
    """

    def __call__(self, serializer_field):
        return super().__call__(serializer_field).date()


class UserTimezoneAwareFieldMixin:
    def _transform(self, value, **kwargs):
        assert 'request' in self.context, \
            "The request must be provided in context when using this default."
        if value is not None:
            return self.context['request'].user.in_timezone(value, **kwargs)
        return value

    def to_representation(self, value, **kwargs):
        obj = super().to_representation(value)
        return self._transform(obj, **kwargs)

    def to_internal_value(self, obj, **kwargs):
        value = super().to_internal_value(obj)
        return self._transform(value, **kwargs)


class UserTimezoneAwareDateField(
        UserTimezoneAwareFieldMixin, serializers.DateField):
    """
    An extension of :obj:`rest_framework.serializers.DateField` that
    incorporates a :obj:`User`'s timezone.
    """

    def __init__(self, *args, **kwargs):
        default_today = kwargs.pop('default_today', False)
        if default_today is True:
            kwargs['default'] = UserDateFieldDefault()
        super().__init__(*args, **kwargs)

    def to_internal_value(self, obj):
        return super().to_internal_value(obj, force_date=True)

    def to_representation(self, value):
        return super().to_representation(value, force_date=True)


class UserTimezoneAwareDateTimeField(
        UserTimezoneAwareFieldMixin, serializers.DateTimeField):
    """
    An extension of :obj:`rest_framework.serializers.DateTimeField` that
    incorporates a :obj:`User`'s timezone.
    """

    def __init__(self, *args, **kwargs):
        default_today = kwargs.pop('default_now', False)
        if default_today is True:
            kwargs['default'] = UserDateTimeFieldDefault()
        super().__init__(*args, **kwargs)


class EmailField(serializers.EmailField):
    def to_representation(self, value):
        value = super().to_representation(value).lower()
        if value is not None:
            return value.lower()
        return value

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        if value is not None:
            return value.lower()
        return value


class UserFilteredQuerysetPKField(serializers.PrimaryKeyRelatedField):
    default_error_messages = {
        **serializers.PrimaryKeyRelatedField.default_error_messages,
        ** {
            'does_not_exist': _(
                'The instance "{pk_value}" - does not belong to the correct '
                'user or does not exist.'
            ),
        }
    }

    def __init__(self, *args, **kwargs):
        self._user_getter = kwargs.pop('user_getter', None)
        self._user_field = kwargs.pop('user_field', 'created_by')
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()

        original_serializer = find_parent_base_serializer(self)

        if self._user_getter is not None:
            user = self._user_getter(original_serializer)
        else:
            request = original_serializer.context.get('request')
            if request is None:
                raise Exception(
                    "The request must be provided in context when using "
                    "the serializer %s."
                    % original_serializer.__class__.__name__
                )
            user = request.user

        # This field can only be used on serializers for authenticated
        # endpoints.
        assert user.is_authenticated is True, "User is not authenticated!"

        filter_kwargs = {self._user_field: user}
        return qs.filter(**filter_kwargs)
