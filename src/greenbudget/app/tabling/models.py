from django.db import models

from greenbudget.app.budgeting.models import (
    BudgetingTreeModel,
    BudgetingModel,
    BudgetingTreePolymorphicModel
)


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

    class Meta:
        abstract = True


class RowModel(RowModelMixin):
    class Meta:
        abstract = True


class BudgetingRowModel(BudgetingModel, RowModelMixin):
    class Meta:
        abstract = True


class BudgetingTreeRowModel(BudgetingTreeModel, RowModelMixin):
    class Meta:
        abstract = True


class BudgetingTreeRowPolymorphicModel(
        BudgetingTreePolymorphicModel, RowModelMixin):

    class Meta:
        abstract = True
