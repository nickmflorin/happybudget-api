import collections
from django.db import models, transaction
from polymorphic.models import PolymorphicManager

from .query import RowQuerySet, RowPolymorphicQuerySet, RowQuerier
from .utils import order_after


class RowManagerMixin(RowQuerier):
    def get_queryset(self):
        return self.queryset_class(self.model)

    @transaction.atomic
    def bulk_create(self, instances, **kwargs):
        # We must lock the rows of the model table that correspond to the
        # individual "tables" we are creating models for, so we do not create
        # additional entries in those table subsets with orders that would cause
        # a unique constraint in this method.
        # TODO: We may need to actually lock the entire table at some point, to
        # prevent bulk additions to the table "table" subset from happening at
        # the same time.
        all_table_instances = self.get_all_in_tables(
            set([obj.table_key for obj in instances])).select_for_update()

        # First, we have to group all of the instances by the tables (or the
        # set of sibling instances in the same table) that they belong to.
        instances_grouped_by_table = collections.defaultdict(list)
        for obj in instances:
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
                orders.append(
                    all_table_instances.get_latest_in_table(table_key).order)
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


class RowManager(RowManagerMixin, models.Manager):
    queryset_class = RowQuerySet


class RowPolymorphicManager(RowManagerMixin, PolymorphicManager):
    queryset_class = RowPolymorphicQuerySet
