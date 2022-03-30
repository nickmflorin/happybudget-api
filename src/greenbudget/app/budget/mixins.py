from django.contrib.contenttypes.models import ContentType
from django.utils.functional import cached_property

from greenbudget.app import mixins, permissions
from greenbudget.app.collaborator.permissions import IsCollaborator

from .models import BaseBudget, Budget
from .permissions import BudgetProductPermission, BudgetOwnershipPermission


class BaseBudgetNestedMixin(mixins.NestedObjectViewMixin):
    """
    A mixin for views that extend off of a budget or template's detail endpoint.
    """
    view_name = "budget"
    budget_permission_classes = [permissions.AND(
        permissions.OR(
            permissions.AND(
                permissions.IsFullyAuthenticated(affects_after=True),
                BudgetOwnershipPermission(affects_after=True),
                BudgetProductPermission(products="__any__"),
            ),
            permissions.AND(
                permissions.IsFullyAuthenticated(affects_after=True),
                IsCollaborator
            ),
            is_object_applicable=lambda c: c.obj.domain == 'budget',
        ),
        permissions.AND(
            permissions.IsFullyAuthenticated(affects_after=True),
            BudgetOwnershipPermission(affects_after=True),
            is_object_applicable=lambda c: c.obj.domain == 'template'
        ),
    )]

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
    budget_permission_classes = [permissions.OR(
        permissions.AND(
            permissions.IsFullyAuthenticated(affects_after=True),
            BudgetOwnershipPermission(affects_after=True),
            BudgetProductPermission(products="__any__"),
        ),
        permissions.AND(
            permissions.IsFullyAuthenticated(affects_after=True),
            IsCollaborator
        ),
        is_object_applicable=lambda c: c.obj.domain == 'budget',
    )]

    def get_budget_queryset(self):
        return Budget.objects.all()


class BaseBudgetPublicNestedMixin(BaseBudgetNestedMixin):
    budget_permission_classes = [permissions.AND(
        permissions.OR(
            permissions.AND(
                permissions.IsFullyAuthenticated(affects_after=True),
                BudgetOwnershipPermission(affects_after=True),
                BudgetProductPermission(products="__any__"),
            ),
            permissions.AND(
                permissions.IsFullyAuthenticated(affects_after=True),
                IsCollaborator
            ),
            permissions.AND(
                permissions.IsSafeRequestMethod,
                permissions.IsPublic,
            ),
            is_object_applicable=lambda c: c.obj.domain == 'budget',
        ),
        permissions.AND(
            permissions.IsFullyAuthenticated(affects_after=True),
            BudgetOwnershipPermission(affects_after=True),
            is_object_applicable=lambda c: c.obj.domain == 'template'
        ),
    )]
