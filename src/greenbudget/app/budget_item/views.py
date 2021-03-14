from rest_framework import viewsets, mixins, decorators

from greenbudget.lib.rest_framework_utils.pagination import paginate_action

from greenbudget.app.account.models import Account
from greenbudget.app.budget.mixins import BudgetNestedMixin

from .serializers import BudgetItemSerializer, BudgetItemTreeNodeSerializer


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

    @decorators.action(methods=["GET"], detail=False)
    @paginate_action(serializer_cls=BudgetItemTreeNodeSerializer)
    def tree(self, request, *args, **kwargs):
        return self.get_queryset().instance_of(Account)


class BudgetItemTreeViewSet(
    mixins.ListModelMixin,
    BudgetNestedMixin,
    viewsets.GenericViewSet
):
    serializer_class = BudgetItemTreeNodeSerializer
    budget_lookup_field = ("pk", "budget_pk")
    search_fields = ['identifier']

    def get_queryset(self):
        return self.budget.items.all()
