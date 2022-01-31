from django.db import models
from polymorphic.models import PolymorphicModel

from greenbudget.lib.utils import ensure_iterable, humanize_list
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
        return {
            pivot: getattr(self, pivot)
            for pivot in ensure_iterable(self.table_pivot)
        }

    @property
    def table_key(self):
        pivot = ensure_iterable(self.table_pivot)
        table_key = [getattr(self, fk_pivot) for fk_pivot in pivot]
        missing_pivots = [
            pivot[i] for i, v in enumerate(table_key) if v is None]
        if missing_pivots:
            raise Exception(
                "Table key cannot be constructed because pivots for fields "
                f"{humanize_list(missing_pivots)} are not defined."
            )
        return tuple(table_key)

    def get_table(self, include_self=True):
        qs = type(self).objects.filter(**self.table_filter)
        if include_self is False:
            return qs.exclude(pk=self.pk).order_with_groups()
        return qs.order_with_groups()

    @property
    def table(self):
        return self.get_table()

    def order_at_bottom(self, commit=True):
        # TODO: At some point, we are going to have to be concerned with locking
        # the table while we retrieve the latest in the table in order to order
        # this instance after it.
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

    def validate_before_save(self, bulk_context=False):
        # If the ordering of the instance is not explicitly defined, default it
        # to being the last in the table.  However, we cannot do this when we
        # are adding multiple models at the same time, because `order_at_bottom`
        # method requires that all the other models be commited to the DB.
        if bulk_context is not True:
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
