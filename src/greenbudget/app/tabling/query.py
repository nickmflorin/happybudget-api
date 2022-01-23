import collections
from django.db import models

from greenbudget.lib.django_utils.query import (
    PrePKBulkCreateQuerySet,
    BulkCreatePolymorphicQuerySet
)
from greenbudget.lib.utils import concat
from .utils import order_after


ModelsAndGroup = collections.namedtuple("ModelsAndGroup", ["models", "group"])


class RowQuerier:
    def reorder(self, commit=True, instances=None):
        instances = instances.all() or self.all()
        ordering = order_after(len(instances))
        [
            setattr(instances[i], "order", ordering[i])
            for i in range(len(instances))
        ]
        if commit:
            self.bulk_update(
                instances, ["order"], batch_size=len(instances))
        return instances

    def reorder_by(self, *fields, commit=True):
        return self.reorder(commit=commit, instances=self.order_by(*fields))

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
            pk=pk, then=pos) for pos, pk in enumerate(ordered)])
        return self.order_by(preserved)


class RowQuerySet(RowQuerier, PrePKBulkCreateQuerySet):
    pass


class RowPolymorphicQuerySet(RowQuerier, BulkCreatePolymorphicQuerySet):
    pass
