from rest_framework import viewsets, mixins

from greenbudget.app.budget.mixins import BudgetNestedMixin

from .models import Account, AccountGroup
from .serializers import AccountSerializer, AccountGroupSerializer


class AccountGroupViewSet(
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """
    Viewset to handle requests to the following endpoints:

    (1) PATCH /accounts/groups/<pk>/
    (2) GET /accounts/groups/<pk>/
    (3) DELETE /accounts/groups/<pk>/
    """
    lookup_field = 'pk'
    serializer_class = AccountGroupSerializer

    def get_queryset(self):
        return AccountGroup.objects.all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class BudgetAccountGroupViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    BudgetNestedMixin,
    viewsets.GenericViewSet
):
    """
    Viewset to handle requests to the following endpoints:

    (1) POST /budgets/<pk>/groups/
    (2) GET /budgets/<pk>/groups/
    """
    lookup_field = 'pk'
    serializer_class = AccountGroupSerializer
    budget_lookup_field = ("pk", "budget_pk")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(parent=self.budget)
        return context

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            budget=self.budget
        )


class GenericAccountViewSet(viewsets.GenericViewSet):
    lookup_field = 'pk'
    serializer_class = AccountSerializer
    ordering_fields = ['updated_at', 'name', 'created_at']
    search_fields = ['name']

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            request=self.request,
            user=self.request.user,
        )
        return context


class AccountViewSet(
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    GenericAccountViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /accounts/<pk>/
    (2) PATCH /accounts/<pk>/
    (3) DELETE /accounts/<pk>/
    """

    def get_queryset(self):
        return Account.objects.filter(budget__trash=False)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class BudgetAccountViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    BudgetNestedMixin,
    GenericAccountViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /budgets/<pk>/accounts/
    (2) POST /budgets/<pk>/accounts/
    """
    budget_lookup_field = ("pk", "budget_pk")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(budget=self.budget)
        return context

    def get_queryset(self):
        return Account.objects.filter(budget=self.budget).all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(
            updated_by=self.request.user,
            created_by=self.request.user,
            budget=self.budget
        )
