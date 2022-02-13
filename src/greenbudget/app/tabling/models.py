import copy

from django.db import models
from polymorphic.models import PolymorphicModel

from greenbudget.lib.utils import (
    ensure_iterable, humanize_list, get_attribute, empty)
from .utils import lexographic_midpoint, validate_order


class RowModelMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        to='user.User',
        related_name='updated_%(class)ss',
        on_delete=models.CASCADE,
        editable=False
    )
    created_by = models.ForeignKey(
        to='user.User',
        related_name='created_%(class)ss',
        on_delete=models.CASCADE,
        editable=False
    )

    class Meta:
        abstract = True

    @property
    def table_pivot(self):
        raise NotImplementedError()

    @property
    def table_filter(self):
        return self.get_table_filter(self)

    @classmethod
    def get_table_filter(cls, *args, **kwargs):
        """
        Returns the queryset filter that is used to select all of the related
        models belonging to the same "table", based on the `table_pivot` defined
        on the model class and the values corresponding to the fields of the
        `table_pivot` provided to this method.

        The values corresponding to the fields of the `table_pivot` can either
        be provided as the model instance, a :obj:`dict` instance or a set of
        keyword arguments.  The reason for this flexibility is that there are
        cases when we need to retrieve the table instances before the additional
        instance is created - in which case we can supply the values as a
        mapping.
        """
        assert (len(args) == 1 and isinstance(args[0], (cls, dict))) or kwargs, \
            "Either the current instance or the data used to create the " \
            "instance must be provided to get the table filter."

        if not hasattr(cls, 'table_pivot'):
            raise Exception(f"Model {cls.__name__} does not define table pivot.")

        if 'table_key' in kwargs:
            table_key = kwargs.pop('table_key')
            if len(table_key) != len(cls.table_pivot):
                raise ValueError("Invalid table key %s provided." % table_key)
            return models.Q(**{
                cls.table_pivot[i]: pivot_value
                for i, pivot_value in enumerate(table_key)
            })

        getter_kwargs = copy.deepcopy(kwargs)
        getter_kwargs.update(default=empty, strict=False)

        query_kwargs = {
            k: get_attribute(k, *args, **getter_kwargs)
            for k in ensure_iterable(cls.table_pivot)
        }
        missing_pivots = [k for k, v in query_kwargs.items() if v is empty]
        if missing_pivots:
            raise Exception(
                "Table filter cannot be constructed because pivots for fields "
                f"{humanize_list(missing_pivots)} are not defined."
            )
        return models.Q(**query_kwargs)

    @property
    def table_key(self):
        return self.get_table_key(self)

    @classmethod
    def get_table_key(cls, *args, **kwargs):
        """
        Returns the tuple of values corresponding to the iterable of fields
        that comprise the `table_pivot` defined on the class, for either a
        instance of the class or a mapping - provided as an :obj:`dict` instance
        or a set of keyword arguments.
        """
        assert (len(args) == 1 and isinstance(args[0], (cls, dict))) or kwargs, \
            "Either the current instance or the data used to create the " \
            "instance must be provided to get the table key."

        if not hasattr(cls, 'table_pivot'):
            raise Exception(f"Model {cls.__name__} does not define table pivot.")

        getter_kwargs = copy.deepcopy(kwargs)
        getter_kwargs.update(default=empty, strict=False)

        table_key = [
            get_attribute(k, *args, **getter_kwargs)
            for k in ensure_iterable(cls.table_pivot)
        ]
        missing_pivots = [k for k in table_key if k is empty]
        if missing_pivots:
            raise Exception(
                "Table key cannot be constructed because pivots for fields "
                f"{humanize_list(missing_pivots)} are not defined."
            )
        return tuple(table_key)

    @classmethod
    def get_table(cls, *args, **kwargs):
        """
        Returns the queryset that filters instances the class that belong to
        the same "table" - which is determined by the instances that have the
        same table-key(s).
        """
        query = cls.get_table_filter(*args, **kwargs)
        return cls.objects.filter(query)

    @property
    def table(self):
        return self.get_table(self)


class OrderedRowModelMixin(RowModelMixin):
    order = models.CharField(
        editable=False,
        max_length=1024,
        blank=False,
        null=False,
        default=None
    )

    class Meta:
        abstract = True

    def order_at_bottom(self):
        try:
            last_in_table = self.table.latest()
        except self.DoesNotExist:
            self.order = lexographic_midpoint()
        else:
            if last_in_table.pk == self.pk:
                return
            self.order = lexographic_midpoint(lower=last_in_table.order)

    def validate_before_save(self):
        if self.order is None:
            self.order_at_bottom()
        validate_order(self.order)

    @classmethod
    def get_table(cls, *args, **kwargs):
        return super(OrderedRowModelMixin, cls) \
            .get_table(*args, **kwargs).order_with_groups()


class RowModel(RowModelMixin):
    class Meta:
        abstract = True


class OrderedRowModel(OrderedRowModelMixin):
    class Meta:
        abstract = True


class RowPolymorphicModel(PolymorphicModel, RowModelMixin):
    class Meta:
        abstract = True


class OrderedRowPolymorphicModel(PolymorphicModel, OrderedRowModelMixin):
    class Meta:
        abstract = True
