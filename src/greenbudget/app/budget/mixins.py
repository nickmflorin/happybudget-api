from django.contrib.contenttypes.models import ContentType
from django.utils.functional import cached_property

from greenbudget.app.budgeting.mixins import NestedObjectViewMixin

from .models import Budget
from .permissions import BudgetSubscriptionPermission


class BudgetNestedMixin(NestedObjectViewMixin):
    """
    A mixin for views that extend off of a budget's detail endpoint.
    """
    budget_permission_classes = [
        BudgetSubscriptionPermission
    ]
    view_name = "budget"
    budget_lookup_field = ("pk", "budget_pk")

    def get_budget_queryset(self, request):
        return Budget.objects.filter(created_by=request.user).all()

    @cached_property
    def content_type(self):
        return ContentType.objects.get_for_model(type(self.budget))
