from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from greenbudget.lib.drf.fields import find_parent_base_serializer
from greenbudget.lib.drf.serializers import LazyContext


class TablePrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    default_error_messages = {
        'does_not_exist_in_table': _(
            'The child {obj_name} with ID {pk_value} does not belong to the '
            'correct table.'
        ),
    }

    def __init__(self, *args, **kwargs):
        self._table_filter = kwargs.pop('table_filter')
        self._table_instance_cls = kwargs.pop('table_instance_cls', None)
        super().__init__(*args, **kwargs)

    @property
    def base_serializer(self):
        base = find_parent_base_serializer(self)
        assert isinstance(base, serializers.ModelSerializer), \
            "This related field must be used with ModelSerializer's only."
        return base

    @property
    def lazy_context(self):
        return LazyContext(self.base_serializer, ref=type(self).__name__)

    @property
    def table_instance_cls(self):
        if self._table_instance_cls is not None:
            if isinstance(self._table_instance_cls, type):
                table_cls = self._table_instance_cls
            else:
                try:
                    table_cls = self._table_instance_cls(self.lazy_context)
                except TypeError:
                    raise TypeError(
                        "`child_instance_cls` must either be a callable "
                        "taking serializer context as it's first and only "
                        "argument, or a class type."
                    )
        else:
            table_cls = self.base_serializer.Meta.model
        assert hasattr(table_cls, 'get_table'), \
            f"Table instance class {table_cls} is not a model class that " \
            "supports tabling."
        return table_cls

    def get_queryset(self):
        context = LazyContext(self.parent, ref=type(self).__name__)
        filter_data = self._table_filter(context)
        return self.table_instance_cls.get_table(**filter_data)

    def to_internal_value(self, data):
        if self.pk_field is not None:
            data = self.pk_field.to_internal_value(data)
        queryset = self.get_queryset()
        try:
            if isinstance(data, bool):
                raise TypeError
            return queryset.get(pk=data)
        except ObjectDoesNotExist:
            # If the object does not exist, we want to indicate in the error
            # message whether or not it does not exist at all or whether it
            # exists but does not belong to the correct table.
            try:
                self.table_instance_cls.objects.get(pk=data)
            except ObjectDoesNotExist:
                self.fail('does_not_exist', pk_value=data)
            else:
                self.fail(
                    'does_not_exist_in_table',
                    pk_value=data,
                    obj_name=getattr(
                        self.table_instance_cls._meta,
                        "verbose_name",
                        "instance"
                    ).lower(),
                )
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data).__name__)
