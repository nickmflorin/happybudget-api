from greenbudget.app.budgeting.mixins import NestedObjectViewMixin

from .models import Budget
from .permissions import BudgetObjPermission


class BudgetNestedMixin(NestedObjectViewMixin):
    """
    A mixin for views that extend off of a budget's detail endpoint.
    """
    budget_permission_classes = [BudgetObjPermission]
    view_name = "budget"

    def get_budget_queryset(self, request):
        return Budget.objects.all()
