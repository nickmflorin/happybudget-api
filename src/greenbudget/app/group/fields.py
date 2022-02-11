from django.utils.translation import gettext_lazy as _
from greenbudget.app.tabling.fields import TablePrimaryKeyRelatedField

from .models import Group


class GroupField(TablePrimaryKeyRelatedField):
    default_error_messages = {
        'is_empty': _(
            'The group with ID {pk_value} is empty and cannot be assigned.'
        ),
    }

    def __init__(self, *args, **kwargs):
        kwargs['table_instance_cls'] = Group
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        instance = super().to_internal_value(data)
        if instance.children.count() == 0:
            self.fail('is_empty', pk_value=instance.pk)
        return instance
