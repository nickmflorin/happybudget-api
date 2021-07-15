from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from greenbudget.lib.drf.fields import find_field_original_serializer


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

    def get_queryset(self, budget=None):
        qs = super().get_queryset()

        original_serializer = find_field_original_serializer(self)
        if original_serializer is None:
            raise Exception("Invalid use of %s." % self.__class__.__name__)

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
