from django.contrib.contenttypes.models import ContentType
from rest_framework import viewsets, mixins, decorators, response, status

from greenbudget.app.account.mixins import AccountNestedMixin
from greenbudget.app.budget.mixins import BudgetNestedMixin
from greenbudget.app.subaccount.models import SubAccountGroup
from greenbudget.app.subaccount.serializers import SubAccountGroupSerializer

from .models import Account, AccountGroup
from .serializers import (
    AccountSerializer,
    AccountGroupSerializer,
    AccountBulkUpdateSubAccountsSerializer,
    AccountBulkCreateSubAccountsSerializer
)


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


class AccountSubAccountGroupViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    AccountNestedMixin,
    viewsets.GenericViewSet
):
    """
    Viewset to handle requests to the following endpoints:

    (1) POST /accounts/<pk>/groups/
    (2) GET /accounts/<pk>/groups/
    """
    lookup_field = 'pk'
    serializer_class = SubAccountGroupSerializer
    account_lookup_field = ("pk", "account_pk")

    def get_queryset(self):
        return SubAccountGroup.objects.filter(
            content_type=ContentType.objects.get_for_model(Account),
            object_id=self.account.pk,
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(parent=self.account)
        return context

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            object_id=self.account.pk,
            content_type=ContentType.objects.get_for_model(Account),
            parent=self.account
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
    (4) PATCH /accounts/<pk>/bulk-update-subaccounts/
    """

    def get_queryset(self):
        return Account.objects.filter(budget__trash=False)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @decorators.action(
        detail=True, url_path='bulk-update-subaccounts', methods=["PATCH"])
    def bulk_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = AccountBulkUpdateSubAccountsSerializer(
            instance=instance,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(updated_by=request.user)
        return response.Response(
            self.serializer_class(instance).data,
            status=status.HTTP_200_OK
        )


class BudgetAccountViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    BudgetNestedMixin,
    GenericAccountViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /budgets/<pk>/accounts/
    (2) POST /budgets/<pk>/accounts/
    (3) PATCH /budgets/<pk>/accounts/<pk>/bulk-create-subaccounts/
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

    @decorators.action(
        detail=True, url_path='bulk-create-subaccounts', methods=["PATCH"])
    def bulk_create(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = AccountBulkCreateSubAccountsSerializer(
            instance=instance,
            data=request.data,
            partial=True,
            context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(updated_by=request.user)
        return response.Response(
            self.serializer_class(instance).data,
            status=status.HTTP_201_CREATED
        )
