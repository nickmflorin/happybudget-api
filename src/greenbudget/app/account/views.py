from django.contrib.contenttypes.models import ContentType
from django.utils.functional import cached_property
from rest_framework import viewsets, mixins, decorators, response, status

from greenbudget.app.account.models import Account
from greenbudget.app.account.mixins import AccountNestedMixin
from greenbudget.app.budget.mixins import BudgetNestedMixin
from greenbudget.app.group.models import (
    BudgetSubAccountGroup,
    TemplateSubAccountGroup
)
from greenbudget.app.group.serializers import (
    BudgetSubAccountGroupSerializer,
    TemplateSubAccountGroupSerializer
)
from greenbudget.app.subaccount.models import (
    BudgetSubAccount, TemplateSubAccount)
from greenbudget.app.subaccount.serializers import (
    BudgetSubAccountSerializer,
    TemplateSubAccountSerializer,
    create_bulk_create_subaccounts_serializer,
    create_bulk_update_subaccounts_serializer
)
from greenbudget.app.template.mixins import TemplateNestedMixin

from .models import BudgetAccount, TemplateAccount
from .serializers import BudgetAccountSerializer, TemplateAccountSerializer


class AccountGroupViewSet(
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
    account_lookup_field = ("pk", "account_pk")

    @cached_property
    def instance_cls(self):
        mapping = {
            BudgetAccount: BudgetSubAccountGroup,
            TemplateAccount: TemplateSubAccountGroup
        }
        return mapping[type(self.account)]

    def get_serializer_class(self):
        mapping = {
            BudgetAccount: BudgetSubAccountGroupSerializer,
            TemplateAccount: TemplateSubAccountGroupSerializer
        }
        return mapping[type(self.account)]

    def get_queryset(self):
        return self.instance_cls.objects.filter(
            content_type=ContentType.objects.get_for_model(type(self.account)),
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
            content_type=ContentType.objects.get_for_model(type(self.account)),
            parent=self.account
        )


class GenericAccountViewSet(viewsets.GenericViewSet):
    lookup_field = 'pk'
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
    (5) PATCH /accounts/<pk>/bulk-create-subaccounts/
    """
    @cached_property
    def instance_cls(self):
        instance = self.get_object()
        return type(instance)

    @property
    def child_instance_cls(self):
        if self.instance_cls is BudgetAccount:
            return BudgetSubAccount
        return TemplateSubAccount

    def get_queryset(self):
        return Account.objects.filter(budget__trash=False)

    def get_serializer_class(self):
        if self.instance_cls is TemplateAccount:
            return TemplateAccountSerializer
        return BudgetAccountSerializer

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_bulk_change(self, serializer_cls, request):
        instance = self.get_object()
        serializer = serializer_cls(
            instance=instance,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        return serializer.save(updated_by=request.user)

    @decorators.action(
        detail=True, url_path='bulk-update-subaccounts', methods=["PATCH"])
    def bulk_update_subaccounts(self, request, *args, **kwargs):
        serializer_cls = create_bulk_update_subaccounts_serializer(
            self.child_instance_cls)
        instance = self.perform_bulk_change(serializer_cls, request)
        serializer_cls = self.get_serializer_class()
        return response.Response(
            serializer_cls(instance).data,
            status=status.HTTP_200_OK
        )

    @decorators.action(
        detail=True, url_path='bulk-create-subaccounts', methods=["PATCH"])
    def bulk_create_subaccounts(self, request, *args, **kwargs):
        serializer_cls = create_bulk_create_subaccounts_serializer(
            self.child_instance_cls)
        subaccounts = self.perform_bulk_change(serializer_cls, request)
        response_serializer_cls = BudgetSubAccountSerializer
        if self.child_instance_cls is TemplateSubAccount:
            response_serializer_cls = TemplateSubAccountSerializer
        return response.Response(
            {'data': response_serializer_cls(subaccounts, many=True).data},
            status=status.HTTP_201_CREATED
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
    """
    budget_lookup_field = ("pk", "budget_pk")
    serializer_class = BudgetAccountSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(budget=self.budget)
        return context

    def get_queryset(self):
        return BudgetAccount.objects.filter(budget=self.budget).all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(
            updated_by=self.request.user,
            created_by=self.request.user,
            budget=self.budget
        )


class TemplateAccountViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    TemplateNestedMixin,
    GenericAccountViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /templates/<pk>/accounts/
    (2) POST /templates/<pk>/accounts/
    """
    template_lookup_field = ("pk", "template_pk")
    serializer_class = TemplateAccountSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(budget=self.template)
        return context

    def get_queryset(self):
        return TemplateAccount.objects.filter(budget=self.template).all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(
            updated_by=self.request.user,
            created_by=self.request.user,
            budget=self.template
        )
