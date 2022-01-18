from django.db import models
from polymorphic.models import PolymorphicManager

from greenbudget.lib.utils import ensure_iterable

from .query import RowQuerySet, RowPolymorphicQuerySet, RowQuerier
from .utils import order_after


class RowManagerMixin(RowQuerier):
    def get_queryset(self):
        return self.queryset_class(self.model)

    def bulk_create(self, instances, **kwargs):
        # First, we have to group all of the instances by the tables (or the
        # set of sibling instances in the same table) that they belong to.
        instances_grouped_by_table = {}
        for obj in instances:
            instances_grouped_by_table.setdefault(obj.table_key, [])
            instances_grouped_by_table[obj.table_key].append(obj)

        # For each individual set of sibling instances, we need to perform the
        # ordering of the new instances based on the ordering already present
        # in the set of sibling instances.
        for table_key, table_instances in instances_grouped_by_table.items():
            # When determining what order each element should have, we not only
            # have to look in the database for the latest order but we also
            # have to include any potential order's that are unsaved on the
            # instances being created.
            orders = [
                instance.order for instance in table_instances
                if instance.order is not None
            ]
            try:
                orders.append(self.get_latest_in_table(table_key).order)
            except self.model.DoesNotExist:
                pass
            last_order = None
            if orders:
                last_order = sorted(orders)[-1]
            # Order the instances that do not have a defined order in the order
            # that they are being created in.
            instances_without_ordering = [
                instance for instance in table_instances
                if instance.order is None
            ]
            ordering = order_after(
                len(instances_without_ordering), last_order=last_order)
            index = 0
            for instance in table_instances:
                if instance.order is None:
                    instance.order = ordering[index]
                    index += 1

        return super().bulk_create(instances, **kwargs)

    def evaluate_table_pivot_filter(self, **kwargs):
        pivot_filter = {}
        for _, pivot_name in enumerate(self.model.table_pivot):
            if pivot_name not in kwargs:
                raise ValueError(
                    "Must provide pivot %s to retrieve table."
                    % pivot_name
                )
            pivot_filter[pivot_name] = kwargs[pivot_name]
        return pivot_filter

    def get_table(self, *args, **kwargs):
        """
        Retrieves the model instances that belong to the table determined by
        the set of arguments provided.

        The arguments can either be provided as:

        (1) Args: The Table Key
            The tuple representation of the field values associated with the
            model table pivot fields.  For instance, if the model has pivot
            fields (content_type_id, object_id), the Table Key should be
            provided as ((5, 10)) (as an example).

        (2) Kwargs: The Table Filter
            The keyword arguments that are used to filter the model instances
            to retrieve the instances that belong to a given table.  For
            instance, if the model has pivot fields (content_type_id, object_id),
            the keyword arguments should be provided as
            (content_type_id=5, object_id=10) (as an example).
        """
        pivot_filter = {}
        if args:
            table_key = args[0]
            if len(table_key) != len(self.model.table_pivot):
                raise ValueError("Invalid table key %s provided." % table_key)
            for i, pivot_value in enumerate(table_key):
                pivot_filter[self.model.table_pivot[i]] = pivot_value
        else:
            pivot_filter = self.evaluate_table_pivot_filter(**kwargs)
        return self.filter(**pivot_filter)

    def get_latest_in_table(self, *args, **kwargs):
        return self.get_table(*args, **kwargs).latest()

    def get_distinct_tables(self):
        fk_pivots = ensure_iterable(self.model.table_pivot)
        fk_pivots = tuple(fk_pivots)

        distinct_filters = [
            self.construct_table_filter(obj)
            for obj in self.order_by(*tuple(fk_pivots))
            .distinct(*tuple(fk_pivots))
        ]
        return [self.filter(**fk_filter) for fk_filter in distinct_filters]

    def reorder_all(self, commit=True):
        updated = []
        for table_qs in self.get_distinct_tables():
            updated += table_qs.reorder(commit=False)
        if commit:
            self.bulk_update(updated, ["order"])
        return updated


class RowManager(RowManagerMixin, models.Manager):
    queryset_class = RowQuerySet


class RowPolymorphicManager(RowManagerMixin, PolymorphicManager):
    queryset_class = RowPolymorphicQuerySet
