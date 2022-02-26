import collections
from django.db import models
from polymorphic.models import PolymorphicManager

from .query import (
    RowQuerySet, RowPolymorphicQuerySet, RowQuerier, OrderedRowQuerier,
    OrderedRowQuerySet, OrderedRowPolymorphicQuerySet)
from .utils import order_after


class RowManagerMixin(RowQuerier):
    def get_queryset(self):
        return self.queryset_class(self.model)


class OrderedRowManagerMixin(OrderedRowQuerier, RowManagerMixin):
    def bulk_create(self, instances, **kwargs):
        """
        Extends traditional bulk create behavior by first establishing the order
        for each instance being bulk created based on the order of the instances
        already persisted to the DB.

        Explicit Ordering
        -----------------
        Before an instance is created, unless it's order is already specified,
        the order must be defaulted such that the instance represents the last
        row in the table subset it belongs to.  We do not, and should not,
        include the order explicitly on any instances being bulk created.

        The only time that we allow the order to be explicitly provided is when
        when we are inserting a single row into the middle of the table - which
        does not leverage the bulk create endpoint behavior.  As such, we enforce
        that the instances being added do not already specify an order, because
        doing so would disrupt the logic.

        Note:
        ----
        When we incorporate multi-user collaboration, we are going to have to
        lock the individual table subsets such that the overall ordering of the
        rows in the table subset is not disrupted when we are determining the
        order of the rows being added.
        """
        assert not any([
            getattr(obj, 'order') is not None for obj in instances]), \
            "Detected instances with ordering already defined.  Explicitly " \
            "ordering instances before a bulk create operation is prohibited."

        # First, we have to group all of the instances by the tables (or the
        # set of sibling instances in the same table) that they belong to.
        instances_grouped_by_table = collections.defaultdict(list)
        for obj in instances:
            instances_grouped_by_table[obj.table_key].append(obj)

        # For each individual set of sibling instances, we need to perform the
        # ordering of the new instances based on the ordering already present
        # in the set of sibling instances.
        for table_key, table_instances in instances_grouped_by_table.items():
            existing_table_instances = self.get_table(table_key)
            # When determining what order each element should have, we have to
            # look in the database for the latest order of the instances in the
            # table subset.
            last_order = None
            try:
                last_in_table = existing_table_instances.latest()
            except self.model.DoesNotExist:
                pass
            else:
                last_order = last_in_table.order

            # Order the instances that do not have a defined order in the order
            # that they are being created in.
            ordering = order_after(len(table_instances), last_order=last_order)
            for i, instance in enumerate(table_instances):
                instance.order = ordering[i]

        return super().bulk_create(instances, **kwargs)


class RowManager(RowManagerMixin, models.Manager):
    queryset_class = RowQuerySet


class OrderedRowManager(OrderedRowManagerMixin, models.Manager):
    queryset_class = OrderedRowQuerySet


class RowPolymorphicManager(RowManagerMixin, PolymorphicManager):
    queryset_class = RowPolymorphicQuerySet


class OrderedRowPolymorphicManager(OrderedRowManagerMixin, PolymorphicManager):
    queryset_class = OrderedRowPolymorphicQuerySet
