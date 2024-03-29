from django.utils.translation import gettext_lazy as _

from happybudget.app.fields import DualFilteredPrimaryKeyRelatedField


class TablePrimaryKeyRelatedField(DualFilteredPrimaryKeyRelatedField):
    queryset_error_code = 'does_not_exist_in_table'
    default_error_messages = {
        queryset_error_code: _(
            'The child {obj_name} with ID {pk_value} does not belong to the '
            'correct table.'
        ),
    }
    queryset_filter_name = 'table_filter'
    instance_cls_name = 'table_instance_cls'
