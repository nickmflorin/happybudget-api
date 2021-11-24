from django.db import models
from polymorphic.models import PolymorphicModel

from greenbudget.lib.utils import ensure_iterable
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
    order = models.CharField(
        editable=False,
        max_length=1024,
        blank=False,
        null=False,
        default=None
    )

    class Meta:
        abstract = True

    @property
    def table_pivot(self):
        raise NotImplementedError()

    @property
    def table_filter(self):
        pivot_filter = {}
        for fk_pivot in ensure_iterable(self.table_pivot):
            pivot_filter[fk_pivot] = getattr(self, fk_pivot)
        return pivot_filter

    @property
    def table_key(self):
        table_key = []
        for fk_pivot in ensure_iterable(self.table_pivot):
            table_key.append(getattr(self, fk_pivot))
        return tuple(table_key)

    def get_table(self, include_self=True):
        qs = type(self).objects.filter(**self.table_filter)
        if include_self is False:
            return qs.exclude(pk=self.pk)
        return qs

    def order_at_bottom(self, commit=True):
        try:
            last_in_table = self.get_table().latest()
        except self.DoesNotExist:
            self.order = lexographic_midpoint()
        else:
            if last_in_table.pk == self.pk:
                return
            self.order = lexographic_midpoint(lower=last_in_table.order)

        if commit:
            self.save(update_fields=["order"])

    def validate_before_save(self):
        # If the ordering of the instance is not explicitly defined, default it
        # to being the last in the table.
        if self.order is None:
            self.order_at_bottom(commit=False)
        else:
            validate_order(self.order)


class RowModel(RowModelMixin):
    class Meta:
        abstract = True


class RowPolymorphicModel(PolymorphicModel, RowModelMixin):
    class Meta:
        abstract = True
