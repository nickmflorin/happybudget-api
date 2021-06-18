from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


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

    def get_queryset(self):
        qs = super().get_queryset()

        if self._budget_getter is not None:
            self._budget_getter = self._budget_getter(self.parent)
        else:
            budget = self.parent.context.get('budget')
            if budget is None:
                if self.parent.instance is None:
                    raise Exception(
                        "The budget must be provided in context when using "
                        "the serializer %s in an update context."
                        % self.parent.__class__.__name__
                    )
                budget = getattr(self.parent.instance, self._budget_field)
                if budget is None:
                    raise Exception(
                        "The budget must be present to use this field.")

        filter_kwargs = {self._budget_field: budget}
        return qs.filter(**filter_kwargs)
