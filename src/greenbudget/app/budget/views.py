from django.http import HttpResponse
from rest_framework import viewsets, mixins, response, status, decorators

from greenbudget.app.account.models import BudgetAccount
from greenbudget.app.account.serializers import (
    BudgetAccountSerializer,
    create_bulk_create_accounts_serializer,
    create_bulk_update_accounts_serializer
)
from greenbudget.app.actual.serializers import BulkUpdateActualsSerializer
from greenbudget.app.common.serializers import EntitySerializer
from greenbudget.app.fringe.serializers import (
    FringeSerializer,
    BulkCreateFringesSerializer,
    BulkUpdateFringesSerializer
)
from greenbudget.app.group.models import BudgetAccountGroup
from greenbudget.app.group.serializers import BudgetAccountGroupSerializer
from greenbudget.app.subaccount.models import BudgetSubAccount

from .models import Budget
from .mixins import BudgetNestedMixin, TrashModelMixin
from .serializers import (
    BudgetSerializer, TreeNodeSerializer, BudgetSimpleSerializer)


class LineItemViewSet(
    mixins.ListModelMixin,
    BudgetNestedMixin,
    viewsets.GenericViewSet
):
    """
    Viewset to handle requests to the following endpoints:

    (1) GET /budgets/<pk>/items/
    """
    serializer_class = EntitySerializer
    budget_lookup_field = ("pk", "budget_pk")
    search_fields = ['identifier']

    def list(self, request, *args, **kwargs):
        qs1 = self.filter_queryset(self.budget.accounts.all())
        qs2 = self.filter_queryset(
            BudgetSubAccount.objects.filter(budget=self.budget))
        qs = self.paginate_queryset(list(qs1) + list(qs2))
        serializer = EntitySerializer(qs, many=True)
        return self.get_paginated_response(serializer.data)


class LineItemTreeViewSet(
    mixins.ListModelMixin,
    BudgetNestedMixin,
    viewsets.GenericViewSet
):
    """
    Viewset to handle requests to the following endpoints:

    (1) GET /budgets/<pk>/items/tree/
    """
    serializer_class = TreeNodeSerializer
    budget_lookup_field = ("pk", "budget_pk")
    search_fields = ['identifier']

    def get_queryset(self):
        return self.budget.accounts.all()


class BudgetGroupViewSet(
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
    serializer_class = BudgetAccountGroupSerializer
    budget_lookup_field = ("pk", "budget_pk")

    def get_queryset(self):
        return BudgetAccountGroup.objects.filter(parent=self.budget)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(parent=self.budget)
        return context

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            parent=self.budget
        )


class BudgetFringeViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    BudgetNestedMixin,
    viewsets.GenericViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /budgets/<pk>/fringes/
    (2) POST /budgets/<pk>/fringes/
    """
    lookup_field = 'pk'
    serializer_class = FringeSerializer
    budget_lookup_field = ("pk", "budget_pk")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(budget=self.budget)
        return context

    def get_queryset(self):
        return self.budget.fringes.all()

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user,
            budget=self.budget
        )


class GenericBudgetViewSet(viewsets.GenericViewSet):
    lookup_field = 'pk'
    ordering_fields = ['updated_at', 'name', 'created_at']
    search_fields = ['name']

    def get_serializer_class(self):
        if self.action == 'list':
            return BudgetSimpleSerializer
        return BudgetSerializer

    @property
    def serializer_class(self):
        return self.get_serializer_class()


class BudgetViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    GenericBudgetViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /budgets/
    (2) POST /budgets/
    (3) GET /budgets/<pk>/
    (4) PATCH /budgets/<pk>/
    (5) DELETE /budgets/<pk>/
    (6) PATCH /budgets/<pk>/bulk-update-accounts/
    (7) PATCH /budgets/<pk>/bulk-create-accounts/
    (8) PATCH /budgets/<pk>/bulk-update-actuals/
    (9) PATCH /budgets/<pk>/bulk-update-fringes/
    (10) PATCH /budgets/<pk>/bulk-create-fringes/
    (11) GET /budgets/<pk>/pdf/
    (12) POST /budgets/<pk>/duplicate/
    """

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            request=self.request,
            user=self.request.user,
        )
        return context

    def get_queryset(self):
        return self.request.user.budgets.instance_of(Budget).active()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.to_trash()
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_bulk_accounts_change(self, serializer_cls, request):
        instance = self.get_object()
        serializer = serializer_cls(
            instance=instance,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        return serializer.save(updated_by=request.user)

    @decorators.action(
        detail=True, url_path='bulk-update-accounts', methods=["PATCH"])
    def bulk_update_accounts(self, request, *args, **kwargs):
        serializer_cls = create_bulk_update_accounts_serializer(BudgetAccount)
        instance = self.perform_bulk_accounts_change(serializer_cls, request)
        return response.Response(
            self.serializer_class(instance).data,
            status=status.HTTP_200_OK
        )

    @decorators.action(
        detail=True, url_path='bulk-create-accounts', methods=["PATCH"])
    def bulk_create_budget_accounts(self, request, *args, **kwargs):
        serializer_cls = create_bulk_create_accounts_serializer(BudgetAccount)
        accounts = self.perform_bulk_accounts_change(serializer_cls, request)
        return response.Response(
            {'data': BudgetAccountSerializer(accounts, many=True).data},
            status=status.HTTP_201_CREATED
        )

    @decorators.action(
        detail=True, url_path='bulk-update-actuals', methods=["PATCH"])
    def bulk_update_actuals(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = BulkUpdateActualsSerializer(
            instance=instance,
            data=request.data,
            partial=True,
            context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(updated_by=request.user)
        return response.Response(
            self.serializer_class(instance).data,
            status=status.HTTP_200_OK
        )

    @decorators.action(
        detail=True, url_path='bulk-update-fringes', methods=["PATCH"])
    def bulk_update_fringes(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = BulkUpdateFringesSerializer(
            instance=instance,
            data=request.data,
            partial=True,
            context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(updated_by=request.user)
        return response.Response(
            self.serializer_class(instance).data,
            status=status.HTTP_200_OK
        )

    @decorators.action(
        detail=True, url_path='bulk-create-fringes', methods=["PATCH"])
    def bulk_create_fringes(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = BulkCreateFringesSerializer(
            instance=instance,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        fringes = serializer.save(updated_by=request.user)
        return response.Response(
            {'data': FringeSerializer(fringes, many=True).data},
            status=status.HTTP_201_CREATED
        )

    @decorators.action(detail=True, methods=["GET"])
    def pdf(self, request, *args, **kwargs):
        instance = self.get_object()
        pdf = instance.to_pdf()
        return HttpResponse(pdf.getvalue(), content_type='application/pdf')

    @decorators.action(detail=True, methods=["POST"])
    def duplicate(self, request, *args, **kwargs):
        instance = self.get_object()
        duplicated = Budget.objects.create(
            original=instance, created_by=request.user)
        return response.Response(
            self.serializer_class(duplicated).data,
            status=status.HTTP_201_CREATED
        )


class BudgetTrashViewSet(TrashModelMixin, GenericBudgetViewSet):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /budgets/trash/
    (2) GET /budgets/trash/<pk>/
    (3) PATCH /budgets/trash/<pk>/restore/
    (4) DELETE /budgets/trash/<pk>/
    """

    def get_queryset(self):
        return self.request.user.budgets.instance_of(Budget).inactive()
