from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from greenbudget.lib.drf.fields import find_field_original_serializer


class BudgetFilteredQuerysetPKField(serializers.PrimaryKeyRelatedField):
    default_error_messages = {
        **serializers.PrimaryKeyRelatedField.default_error_messages,
        ** {
            'does_not_exist': _(
                'The instance "{pk_value}" does not belong to the correct '
                'budget.'
            ),
        }
    }

    def __init__(self, *args, **kwargs):
        self._apply_filter = kwargs.pop('apply_filter', None)
        self._budget_getter = kwargs.pop('budget_getter', None)
        self._object_name = kwargs.pop('object_name', None)
        if self._object_name is not None:
            self.default_error_messages['does_not_exist'] = _(
                'The %s "{pk_value}" does not belong to the correct '
                'budget.' % self._object_name
            )
        self._budget_field = kwargs.pop('budget_field', 'budget')
        super().__init__(*args, **kwargs)

    def get_queryset(self, budget=None):
        qs = super().get_queryset()

        original_serializer = find_field_original_serializer(self)
        if original_serializer is None:
            raise Exception("Invalid use of %s." % self.__class__.__name__)

        # We allow the budget to be explicitly passed in for serializer fields
        # that extend this one.
        if budget is None:
            if self._budget_getter is not None:
                budget = self._budget_getter(original_serializer)
            else:
                budget = original_serializer.context.get('budget')
                if budget is None:
                    if original_serializer.instance is None:
                        raise Exception(
                            "The budget must be provided in context when using "
                            "the serializer %s in an update context."
                            % original_serializer.__class__.__name__
                        )
                    budget = getattr(original_serializer.instance,
                                    self._budget_field)

        if budget is None:
            raise Exception("The budget must be present to use this field.")

        if self._apply_filter is not None:
            return self._apply_filter(qs, budget)

        filter_kwargs = {self._budget_field: budget}
        return qs.filter(**filter_kwargs)


class ContextParentMixin:

    def get_parent(self):
        original_serializer = find_field_original_serializer(self)
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


class AccountChildrenFilteredQuerysetPKField(
        ContextParentMixin, BudgetFilteredQuerysetPKField):
    """
    A :obj:`serializers.PrimaryKeyRelatedField` that ensures that the children
    :obj:`Account`(s) provided in the request belong to the same
    :obj:`budget.Budget` as the object we are updating.
    """
    default_error_messages = {
        **serializers.PrimaryKeyRelatedField.default_error_messages,
        ** {
            'does_not_exist': _(
                'The instance "{pk_value}" does not belong to the correct '
                'parent.'
            ),
        }
    }

    def __init__(self, *args, **kwargs):
        self._parent_getter = kwargs.pop('parent_getter', None)
        self._parent_field = kwargs.pop('parent_field', 'parent')
        super().__init__(*args, **kwargs)

        if self._object_name is not None:
            self.default_error_messages['does_not_exist'] = _(
                'The %s "{pk_value}" does not belong to the correct '
                'budget.' % self._object_name
            )
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        parent = self.get_parent()
        return super().get_queryset(budget=parent)


class SubAccountChildrenFilteredQuerysetPKField(
        ContextParentMixin, serializers.PrimaryKeyRelatedField):
    """
    A :obj:`serializers.PrimaryKeyRelatedField` that ensures that the children
    :obj:`SubAccount`(s) provided in the request belong to the same
    parent as the object we are updating.
    """
    default_error_messages = {
        **serializers.PrimaryKeyRelatedField.default_error_messages,
        ** {
            'does_not_exist': _(
                'The instance "{pk_value}" does not belong to the correct '
                'parent.'
            ),
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._parent_getter = kwargs.pop('parent_getter', None)
        self._parent_field = kwargs.pop('parent_field', 'parent')

        self._object_name = kwargs.pop('object_name', None)
        if self._object_name is not None:
            self.default_error_messages['does_not_exist'] = _(
                'The %s "{pk_value}" does not belong to the correct '
                'budget.' % self._object_name
            )
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        parent = self.get_parent()
        qs = super().get_queryset()
        return qs.filter(
            content_type=ContentType.objects.get_for_model(type(parent)),
            object_id=parent.pk
        )
