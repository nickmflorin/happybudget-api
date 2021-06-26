from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from greenbudget.app.budget.fields import (
    BudgetFilteredQuerysetPKField, find_original_serializer)


class AccountGroupChildFilteredQuerysetPKField(BudgetFilteredQuerysetPKField):
    default_error_messages = {
        **serializers.PrimaryKeyRelatedField.default_error_messages,
        ** {
            'does_not_exist': _(
                'The instance "{pk_value}" - does not belong to the correct '
                'budget or parent.'
            ),
        }
    }

    def __init__(self, *args, **kwargs):
        self._parent_getter = kwargs.pop('parent_getter', None)
        self._parent_field = kwargs.pop('parent_field', 'parent')
        super().__init__(*args, **kwargs)

        if self._object_name is not None:
            self.default_error_messages['does_not_exist'] = _(
                'The %s "{pk_value}" - does not belong to the correct '
                'budget or parent.' % self._object_name
            )
        super().__init__(*args, **kwargs)

    def get_parent(self):
        original_serializer = find_original_serializer(self)
        if original_serializer is None:
            raise Exception("Invalid use of %s." % self.__class__.__name__)

        if self._parent_getter is not None:
            parent = self._parent_getter(original_serializer)
        else:
            parent = original_serializer.context.get('parent')
            if parent is None:
                if original_serializer.instance is None:
                    raise Exception(
                        "The parent must be provided in context when using "
                        "the serializer %s in an update context."
                        % original_serializer.__class__.__name__
                    )
                parent = getattr(original_serializer.instance,
                                 self._parent_field)

        if parent is None:
            raise Exception("The parent must be present to use this field.")
        return parent

    def get_queryset(self, budget=None):
        parent = self.get_parent()
        return super().get_queryset(budget=parent)


class SubAccountGroupChildFilteredQuerysetPKField(
        AccountGroupChildFilteredQuerysetPKField):

    def get_queryset(self):
        parent = self.get_parent()
        qs = super(AccountGroupChildFilteredQuerysetPKField,
                   self).get_queryset(budget=parent.budget)
        return qs.filter(
            content_type=ContentType.objects.get_for_model(type(parent)),
            object_id=parent.pk
        )
