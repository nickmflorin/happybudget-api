from greenbudget.lib.django_utils.models import (
    PrePKBulkCreateQuerySet,
    BulkCreatePolymorphicQuerySet
)
from .utils import order_after


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


class RowQuerySet(RowQuerier, PrePKBulkCreateQuerySet):
    pass


class RowPolymorphicQuerySet(RowQuerier, BulkCreatePolymorphicQuerySet):
    pass
