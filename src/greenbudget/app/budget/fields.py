from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


def find_original_serializer(field):
    parent = field.parent
    while parent is not None:
        new_parent = parent.parent
        if new_parent is None:
            break
        parent = new_parent
    return parent


class BudgetFilteredQuerysetPKField(serializers.PrimaryKeyRelatedField):
    default_error_messages = {
        **serializers.PrimaryKeyRelatedField.default_error_messages,
        ** {
            'does_not_exist': _(
                'The instance "{pk_value}" - does not belong to the correct '
                'budget.'
            ),
        }
    }

    def __init__(self, *args, **kwargs):
        self._budget_getter = kwargs.pop('budget_getter', None)
        self._object_name = kwargs.pop('object_name', None)
        if self._object_name is not None:
            self.default_error_messages['does_not_exist'] = _(
                'The %s "{pk_value}" - does not belong to the correct '
                'budget.' % self._object_name
            )
        self._budget_field = kwargs.pop('budget_field', 'budget')
        super().__init__(*args, **kwargs)

    def get_queryset(self, budget=None):
        qs = super().get_queryset()

        original_serializer = find_original_serializer(self)
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

        filter_kwargs = {self._budget_field: budget}
        return qs.filter(**filter_kwargs)
