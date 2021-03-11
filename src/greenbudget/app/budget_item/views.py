from rest_framework import viewsets, mixins

from greenbudget.app.budget.mixins import BudgetNestedMixin

from .serializers import BudgetItemSerializer


class BudgetItemViewSet(
    mixins.ListModelMixin,
    BudgetNestedMixin,
    viewsets.GenericViewSet
):
    serializer_class = BudgetItemSerializer
    budget_lookup_field = ("pk", "budget_pk")
    search_fields = ['identifier']

    def get_queryset(self):
        return self.budget.items.all()
