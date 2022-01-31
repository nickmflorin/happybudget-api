from django.contrib.contenttypes.models import ContentType
from django.utils.functional import cached_property

from greenbudget.app import mixins, permissions

from .models import Budget
from .permissions import BudgetProductPermission


class BudgetNestedMixin(mixins.NestedObjectViewMixin):
    """
    A mixin for views that extend off of a budget's detail endpoint.
    """
    budget_permission_classes = [
        permissions.IsOwner(object_name='budget', affects_after=True),
        BudgetProductPermission(products="__any__")
    ]
    view_name = "budget"
    budget_lookup_field = ("pk", "budget_pk")

    def get_budget_queryset(self, request):
        return Budget.objects.all()

    @cached_property
    def content_type(self):
        return ContentType.objects.get_for_model(type(self.budget))


class BudgetSharedNestedMixin(BudgetNestedMixin):
    budget_permission_classes = [
        permissions.OR(
            permissions.AND(
                permissions.IsOwner(object_name='budget', affects_after=True),
                BudgetProductPermission(products="__any__")
            ),
            permissions.IsShared,
        )
    ]
