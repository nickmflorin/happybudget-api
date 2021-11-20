from greenbudget.lib.django_utils.models import (
    PrePKBulkCreateQuerySet,
    BulkCreatePolymorphicQuerySet
)
from .utils import order_after, lexographic_midpoint


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

    def get_order_at_integer(self, order, direction):
        assert direction in ('up', 'down'), \
            "The direction must either be provided as `up` or `down`."
        if self.count() == 0:
            return lexographic_midpoint()
        elif order == 0:
            return lexographic_midpoint(upper=self.all()[1].order)
        elif order > self.count():
            return lexographic_midpoint(lower=self.all()[-1].order)
        elif direction == 'down':
            return lexographic_midpoint(
                lower=self.all()[order].order,
                upper=self.all()[order + 1].order
            )
        else:
            return lexographic_midpoint(
                lower=self.all()[order - 1].order,
                upper=self.all()[order].order
            )


class RowQuerySet(RowQuerier, PrePKBulkCreateQuerySet):
    pass


class RowPolymorphicQuerySet(RowQuerier, BulkCreatePolymorphicQuerySet):
    pass
