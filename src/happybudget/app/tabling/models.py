import copy

from django.db import models

from happybudget.lib.utils import (
    ensure_iterable, humanize_list, get_attribute, empty,
    ImmutableAttributeMapping)

from happybudget.app.models import BaseModel
from happybudget.app.user.mixins import ModelOwnershipMixin

from .utils import lexographic_midpoint, validate_order


class TableKey(ImmutableAttributeMapping):
    """
    Defines the field-value pairs that uniquely identify a table subset of the
    corresponding model instances.
    """
    @property
    def fields(self):
        # Sort the fields alphabetically for consistent resolution, hashing and
        # comparison.
        return sorted(list(self.keys()))

    @property
    def values(self):
        # Make sure the values are ordered by the alphabetical order of the
        # keys for consistent resolution, hashing and comparison.
        return tuple([self[k] for k in self.fields])

    @property
    def filter(self):
        return models.Q(**self.data)

    def __eq__(self, other):
        return set(self.values) == set(other.values)

    def __hash__(self):
        return hash(self.values)


class RowModelMixin(ModelOwnershipMixin):
    owner_field = 'created_by'

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

        The values corresponding to the fields of the `table_pivot` can be
        provided in the following ways:

        (1) Model Instance
            In this case, the attributes defined on the model instance
            corresponding to the fields of the `table_pivot` will be used to
            construct the table filter.

        (2) Related Instance
            If the model class defines the method
            `parse_related_model_table_key_data`, then the table key can be
            constructed based on the data parsed from the related instance in
            that method.

        (3) Mapping
            In this case, the values defined on the mapping corresponding to
            the fields of the `table_pivot` will be used to construct the
            table filter.  The mapping can either be provided as **kwargs,
            an :obj:`dict` instance, or an :obj:`TableKey` instance.

        The reason for this flexibility is that there are cases when we need to
        retrieve the table instances before the additional instance is created
        - in which case we can supply the values as a mapping or table key.
        """
        if 'table_key' in kwargs or (len(args) == 1
                and isinstance(args[0], TableKey)):
            table_key = kwargs.pop('table_key', None)
            if not table_key:
                table_key = args[0]

            if isinstance(table_key, TableKey):
                return table_key.filter
        return cls.get_table_key(*args, **kwargs).filter

    @property
    def table_key(self):
        return self.get_table_key(self)

    @classmethod
    def _validate_table_key_data(cls, table_key_data):
        missing_pivots = [
            k for k in table_key_data
            if table_key_data.get(k, empty) is empty
        ]
        if missing_pivots:
            raise Exception(
                "Table key cannot be constructed because pivots for fields "
                f"{humanize_list(missing_pivots)} are not defined."
            )

    @classmethod
    def _instantiate_table_key(cls, *args, **kwargs):
        getter_kwargs = copy.deepcopy(kwargs)
        getter_kwargs.update(default=empty, strict=False)

        table_key = {
            k: get_attribute(k, *args, **getter_kwargs)
            for k in ensure_iterable(cls.table_pivot)
        }
        cls._validate_table_key_data(table_key)
        return TableKey(table_key)

    @classmethod
    def get_table_key(cls, *args, **kwargs):
        """
        Returns the :obj:`TableKey` instance that uniquely identifies the
        instances belonging to the same "table", based on the `table_pivot`
        defined on the model class and the values corresponding to the fields of
        the `table_pivot` provided to this method.

        The values corresponding to the fields of the `table_pivot` can be
        provided in the following ways:

        (1) Model Instance
            In this case, the attributes defined on the model instance
            corresponding to the fields of the `table_pivot` will be used to
            construct the table filter.

        (2) Related Instance
            If the model class defines the method
            `parse_related_model_table_key_data`, then the table key can be
            constructed based on the data parsed from the related instance in
            that method.

        (3) Mapping
            In this case, the values defined on the mapping corresponding to
            the fields of the `table_pivot` will be used to construct the
            table filter.  The mapping can either be provided as **kwargs or
            an :obj:`dict` instance.

        The reason for this flexibility is that there are cases when we need to
        retrieve the table instances before the additional instance is created
        - in which case we can supply the values as a mapping or table key.
        """
        assert len(args) in (0, 1), "Inproper use of this method."

        assert (len(args) == 1
                and isinstance(args[0], (cls, dict, models.Model))) or kwargs, \
            "Either the current instance, the related instance or the data " \
            "used to create the instance must be provided to get the table key."

        assert hasattr(cls, 'table_pivot'), \
            f"Model {cls.__name__} does not define table pivot."

        if args and not isinstance(args[0], cls) \
                and not isinstance(args[0], dict):
            assert hasattr(cls, 'parse_related_model_table_key_data'), \
                f"Model {cls.__name__} does not define the method " \
                "`parse_related_model_table_key_data`, as such, the table key " \
                "cannot be determined from a related model."
            data = cls.parse_related_model_table_key_data(args[0])
            return cls._instantiate_table_key(**data)

        return cls._instantiate_table_key(*args, **kwargs)

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
        # Note: This should never be triggered during bulk create operations,
        # as the order should be defined in the manager logic before the
        # pre-save validation methods are called on the instances.
        if self.order is None:
            self.order_at_bottom()
        validate_order(self.order)

    @classmethod
    def get_table(cls, *args, **kwargs):
        return super(OrderedRowModelMixin, cls) \
            .get_table(*args, **kwargs).order_with_groups()


class RowModel(BaseModel(polymorphic=False), RowModelMixin):
    class Meta:
        abstract = True


class OrderedRowModel(BaseModel(polymorphic=False), OrderedRowModelMixin):
    order = models.CharField(
        editable=False,
        max_length=1024,
        blank=False,
        null=False,
        default=None
    )

    class Meta:
        abstract = True


class OrderedRowPolymorphicModel(
    BaseModel(polymorphic=True),
    OrderedRowModelMixin
):
    order = models.CharField(
        editable=False,
        max_length=1024,
        blank=False,
        null=False,
        default=None
    )

    class Meta:
        abstract = True
