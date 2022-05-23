import collections
from django.db import models, transaction

from happybudget.lib.utils import ensure_iterable, concat
from happybudget.app import query

from .utils import order_after


ModelsAndGroup = collections.namedtuple("ModelsAndGroup", ["models", "group"])


class RowQuerier:
    def get_all_in_tables(self, table_keys):
        """
        Returns a queryset that filters for the model instances belonging to
        all of the tables determined by the set of table keys provided.
        """
        table_keys = ensure_iterable(table_keys)
        assert table_keys, "At least 1 table key must be provided."
        qs_filter = self.model.get_table_filter(table_key=table_keys[0])
        for table_key in table_keys[1:]:
            qs_filter = qs_filter | self.model.get_table_filter(
                table_key=table_key)
        return self.filter(qs_filter)

    def get_table(self, *args, **kwargs):
        return self.model.get_table(*args, **kwargs)

    def get_latest_in_table(self, *args, **kwargs):
        return self.get_table(*args, **kwargs).latest()

    @classmethod
    def get_distinct_table_filters(cls, qs):
        assert isinstance(qs, (list, tuple, models.QuerySet)), \
            "Invalid queryset/iterable provided.  Must be an iterable or an " \
            "instance of `models.QuerySet`."
        if isinstance(qs, models.QuerySet):
            fk_pivots = ensure_iterable(cls.model.table_pivot)
            fk_pivots = tuple(fk_pivots)
            return [
                cls.model.get_table_filter(obj)
                for obj in qs.order_by(*tuple(fk_pivots))
                .distinct(*tuple(fk_pivots))
            ]
        return list(set([obj.table_filter for obj in qs]))

    @classmethod
    def get_distinct_table_keys(cls, qs):
        assert isinstance(qs, (list, tuple, models.QuerySet)), \
            "Invalid queryset/iterable provided.  Must be an iterable or an " \
            "instance of `models.QuerySet`."
        if isinstance(qs, models.QuerySet):
            fk_pivots = ensure_iterable(cls.model.table_pivot)
            fk_pivots = tuple(fk_pivots)
            return [
                cls.model.get_table_key(obj)
                for obj in qs.order_by(*tuple(fk_pivots))
                .distinct(*tuple(fk_pivots))
            ]
        return list(set([obj.table_key for obj in qs]))

    @classmethod
    def get_all_in_same_table(cls, qs):
        assert isinstance(qs, (list, tuple, models.QuerySet)), \
            "Invalid queryset/iterable provided.  Must be an iterable or an " \
            "instance of `models.QuerySet`."
        assert not (
            (isinstance(qs, models.QuerySet) and qs.count() == 0)
            or (isinstance(qs, (tuple, list)) and len(qs) == 0)), \
            "Queryset, tuple or list must be non-empty."
        return len(cls.get_distinct_table_keys(qs)) == 1

    def all_in_same_table(self):
        """
        Returns whether or not the instances of the current :obj:`QuerySet`
        (self) all belong to the same "table" - where the "table" is determined
        by the pivot fields on the model that are used to filter the models
        for a single table.
        """
        return self.get_all_in_same_table(self)

    def distinct_table_keys(self):
        return self.get_distinct_table_keys(self)

    def distinct_tables(self):
        """
        Returns an array of :obj:`QuerySet` instances where each :obj:`QuerySet`
        in the array corresponds to a distinct "table" for at least one of the
        instances in the current :obj:`QuerySet` (self).
        """
        distinct_filters = self.get_distinct_table_filters(self)
        return [self.filter(fk_filter) for fk_filter in distinct_filters]


class OrderedRowQuerier(RowQuerier):
    @transaction.atomic
    def reorder(self, commit=True):
        self.select_for_update()
        ordering = order_after(self.count())

        instances = self.all()
        # TODO: We might want to write this such that it operates on each subset
        # table comprised of the instances individually.
        assert len(set([obj.table_key for obj in instances])) == 1, \
            "Can only reorder instances that all belong to the same table."
        for i in range(self.count()):
            setattr(instances[i], "order", ordering[i])

        if commit:
            self.bulk_update(instances, ["order"], batch_size=len(instances))
        return instances

    def reorder_all(self, commit=True):
        updated = []
        for table_qs in self.distinct_tables():
            updated += table_qs.reorder(commit=False)
        if commit:
            self.bulk_update(updated, ["order"])
        return updated

    def order_with_groups(self):
        """
        When a series of row objects are handled by the FE, the FE determines
        how they should be ordered in the current table based both on:

        (1) The row's `order` field.
        (2) The :obj:`Group` the row may belong to and the order of that
            :obj:`Group` relative to the other :obj:`Group`(s) for other rows
            in that table.

        This is because assigning a row to a :obj:`Group` or unassigning a row
        from a :obj:`Group` affects where that row is displayed in the table.
        In order to do this, the FE needs both the rows to display in the table
        and the :obj:`Group`(s) for all rows in the table themselves.  The FE
        needs to be capable of performing the ordering with :obj:`Group`(s)
        accounted for because when a user makes changes to the grouping or
        ordering of rows, the FE needs to reorder the rows without relying on
        the backend.  However, there are cases where we need to return the
        rows ordered with :obj:`Group`(s) accounted for, because reordering
        by the FE is not applicable and including all of the :obj:`Group`(s)
        in the simple list response would be cumbersome.

        This method is used to order a series of row objects based both on the
        `order` field and the :obj:`Group` they may or may not belong to so that
        the results are ordered the same way that the FE would order them in
        the table.

        The algorithm used to perform this ordering is based on the following
        principles:

        (1) Rows that belong to :obj:`Group`(s) come before rows that do not
            belong to :obj:`Group`(s).  This is because in the FE tables, the
            :obj:`Group` includes all rows above it up until the top of the
            table or the next :obj:`Group`.
        (2) :obj:`Group`(s) are ordered by the lowest order of the rows that
            it contains, because we do not allow a user to reorder
            :obj:`Group`(s).
        (3) The rows in a :obj:`Group` are ordered by the `order` field.
        (4) The rows not in a :obj:`Group` are also ordered by the `order`
            field.

        Example
        -------
        To see this more clearly, consider the following ordering scheme.  Note
        that we use integers for the `order` field instead of alphanumeric
        characters (as they are actually are stored) for purposes of this
        example.

          - Account (order = 3)
          - Account (order = 5)
        - Group
          - Account (order = 7)
          - Account (order = 9)
          - Account (order = 10)
        - Group
        - Account (order = 1)
        - Account (order = 2)
        - Account (order = 4)
        - Account (order = 6)
        - Account (order = 8)
        """
        # We cannot perform the order_by if there are no results in the current
        # queryset because the models.Case() will try to order the queryset by
        # a NULL value, which will hit an SQL error even though there are no
        # results to order.
        if self.count() == 0:
            return self

        # Make sure that all instances belong to the same table.  Unfortunately,
        # a dict is not hashable, so we cannot just check the size of a set.
        table_filter = None

        # pylint: disable=not-an-iterable
        for obj in self:
            if table_filter is not None and obj.table_filter != table_filter:
                raise Exception(
                    "Ordering a queryset with groups accounted for requires "
                    "that all instances belong to the same table."
                )
            else:
                table_filter = obj.table_filter

        models_without_groups = []
        models_with_group = {}

        # pylint: disable=not-an-iterable
        for obj in self:
            # While the FE considers every row object to be groupable, every
            # row object in the backend isn't necessarily groupable.
            if hasattr(obj, 'group_id') and obj.group_id is not None:
                models_with_group.setdefault(obj.group_id, ModelsAndGroup(
                    models=[],
                    group=obj.group
                ))
                models_with_group[obj.group_id].models.append(obj)
            else:
                models_without_groups.append(obj)

        # Sort the ModelsAndGroup instances by the lowest order of it's
        # children rows, and sort the models within each ModelsAndGroup instance
        # by it's order.
        flattened = sorted([
            ModelsAndGroup(
                models=sorted(mg.models, key=lambda obj: obj.order),
                group=mg.group
            )
            for mg in list(models_with_group.values())
        ], key=lambda mg: min([m.order for m in mg.models]))

        ordered = concat([mg.models for mg in flattened]) \
            + models_without_groups

        # We need to return a QuerySet instance, not a list.
        preserved = models.Case(*[models.When(
            pk=obj.pk, then=pos) for pos, obj in enumerate(ordered)])
        return self.order_by(preserved)


class RowQuerySet(RowQuerier, query.QuerySet):
    pass


class OrderedRowQuerySet(OrderedRowQuerier, query.QuerySet):
    pass


class RowPolymorphicQuerySet(RowQuerier, query.PolymorphicQuerySet):
    pass


class OrderedRowPolymorphicQuerySet(
        OrderedRowQuerier, query.PolymorphicQuerySet):
    pass
