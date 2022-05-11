from rest_framework import serializers

from happybudget.app import exceptions


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


class UserAwarePrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    """
    Abstract extension of the serializer field
    :obj:`rest_framework.serializers.PrimaryKeyRelatedField` that implements
    functionality for determining the current request user.

    This field is not meant to be used as a standalone.
    """
    def get_user(self):
        assert 'user' in self.context or 'request' in self.context, \
            f"The serializer using the field {self._class__} must be " \
            "provided with the user or the current request in it's context."
        return self.context.get('user', self.context['request'].user)


class OwnershipPrimaryKeyRelatedField(UserAwarePrimaryKeyRelatedField):
    def to_internal_value(self, data):
        instance = super().to_internal_value(data)
        assert hasattr(instance, 'user_owner'), \
            f"The instance associated with the {self.__class__} field must " \
            "dictate ownership."

        request_user = self.get_user()
        assert request_user.is_fully_authenticated, \
            "Unauthenticated user is performing write methods!"

        if instance.user_owner != request_user:
            raise exceptions.ValidationError(
                "Instance does not belong to the correct user.",
                code='invalid'
            )
        return instance
