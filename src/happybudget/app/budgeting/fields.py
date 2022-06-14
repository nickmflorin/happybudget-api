from django.utils.translation import gettext_lazy as _

from happybudget.app.fields import DualFilteredPrimaryKeyRelatedField


class BudgetRelatedField(DualFilteredPrimaryKeyRelatedField):
    queryset_error_code = 'does_not_belong_to_budget'
    default_error_messages = {
        queryset_error_code: _(
            'The child {obj_name} with ID {pk_value} does not belong to the '
            'correct budget.'
        ),
    }
