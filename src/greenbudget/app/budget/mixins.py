from django.contrib.contenttypes.models import ContentType
from django.utils.functional import cached_property

from greenbudget.app import mixins, permissions
from greenbudget.app.budgeting.permissions import IsTemplateDomain

from .models import BaseBudget, Budget
from .permissions import BudgetProductPermission, BudgetOwnershipPermission


class BaseBudgetNestedMixin(mixins.NestedObjectViewMixin):
    """
    A mixin for views that extend off of a budget or template's detail endpoint.
    """
    budget_permission_classes = [
        BudgetOwnershipPermission(affects_after=True),
        permissions.OR(
            IsTemplateDomain,
            BudgetProductPermission(products="__any__")
        )
    ]
    view_name = "budget"

    @property
    def instance(self):
        return self.budget

    def get_budget_queryset(self):
        return BaseBudget.objects.all()

    @cached_property
    def content_type(self):
        return ContentType.objects.get_for_model(type(self.budget))


class BudgetNestedMixin(BaseBudgetNestedMixin):
    """
    A mixin for views that extend off of a budget's detail endpoint.
    """
    budget_permission_classes = [
        BudgetOwnershipPermission(affects_after=True),
        BudgetProductPermission(products="__any__")
    ]

    def get_budget_queryset(self):
        return Budget.objects.all()


class BaseBudgetSharedNestedMixin(BaseBudgetNestedMixin):
    budget_permission_classes = [
        permissions.OR(
            permissions.AND(
                BudgetOwnershipPermission(affects_after=True),
                permissions.OR(
                    IsTemplateDomain,
                    BudgetProductPermission(products="__any__")
                )
            ),
            permissions.OR(
                IsTemplateDomain,
                permissions.IsShared,
            )
        )
    ]


class BudgetSharedNestedMixin(BudgetNestedMixin):
    budget_permission_classes = [
        permissions.OR(
            permissions.AND(
                BudgetOwnershipPermission(affects_after=True),
                BudgetProductPermission(products="__any__")
            ),
            permissions.IsShared,
        )
    ]
