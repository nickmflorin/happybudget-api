from django.contrib.contenttypes.models import ContentType
from rest_framework import viewsets, mixins

from greenbudget.app.account.models import Account
from greenbudget.app.account.mixins import BudgetAccountNestedMixin

from .mixins import SubAccountNestedMixin
from .models import SubAccount, SubAccountGroup
from .serializers import SubAccountSerializer, SubAccountGroupSerializer


class SubAccountGroupViewSet(
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """
    Viewset to handle requests to the following endpoints:

    (1) PATCH /subaccounts/groups/<pk>/
    (2) GET /subaccounts/groups/<pk>/
    (3) DELETE /subaccounts/groups/<pk>/
    """
    lookup_field = 'pk'
    serializer_class = SubAccountGroupSerializer

    def get_queryset(self):
        return SubAccountGroup.objects.all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class SubAccountSubAccountGroupViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    SubAccountNestedMixin,
    viewsets.GenericViewSet
):
    """
    Viewset to handle requests to the following endpoints:

    (1) POST /subaccounts/<pk>/groups/
    (2) GET /subaccounts/<pk>/groups/
    """
    lookup_field = 'pk'
    serializer_class = SubAccountGroupSerializer
    subaccount_lookup_field = ("pk", "subaccount_pk")

    def get_queryset(self):
        return SubAccountGroup.objects.filter(
            content_type=ContentType.objects.get_for_model(SubAccount),
            object_id=self.subaccount.pk,
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(parent=self.subaccount)
        return context

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            object_id=self.subaccount.pk,
            content_type=ContentType.objects.get_for_model(SubAccount),
            parent=self.subaccount
        )


class GenericSubAccountViewSet(viewsets.GenericViewSet):
    lookup_field = 'pk'
    serializer_class = SubAccountSerializer
    ordering_fields = ['updated_at', 'name', 'created_at']
    search_fields = ['name']


class SubAccountViewSet(
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    GenericSubAccountViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /subaccounts/<pk>/
    (2) PATCH /subaccounts/<pk>/
    (3) DELETE /subaccounts/<pk>/
    """

    def get_serializer_context(self):
        instance = self.get_object()
        context = super().get_serializer_context()
        context.update(budget=instance.budget)
        return context

    def get_queryset(self):
        return SubAccount.objects.filter(budget__trash=False)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class SubAccountRecursiveViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    SubAccountNestedMixin,
    GenericSubAccountViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /subaccounts/<pk>/subaccounts
    (2) POST /subaccounts/<pk>/subaccounts
    """
    subaccount_lookup_field = ("pk", "subaccount_pk")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            parent=self.subaccount,
            budget=self.subaccount.budget
        )
        return context

    def get_queryset(self):
        # The queryset will already be limited to SubAccount(s) that belong
        # to Budget(s) that are not in the Trash, because the @property
        # `account` only looks at active Budget(s).
        content_type = ContentType.objects.get_for_model(SubAccount)
        return SubAccount.objects.filter(
            object_id=self.subaccount.pk,
            content_type=content_type
        )

    def perform_create(self, serializer):
        serializer.save(
            updated_by=self.request.user,
            created_by=self.request.user,
            object_id=self.subaccount.pk,
            content_type=ContentType.objects.get_for_model(SubAccount),
            parent=self.subaccount,
            budget=self.subaccount.budget
        )


class AccountSubAccountViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    BudgetAccountNestedMixin,
    GenericSubAccountViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /budgets/<pk>/accounts/<pk>/subaccounts
    (2) POST /budgets/<pk>/accounts/<pk>/subaccounts
    """
    budget_lookup_field = ("pk", "budget_pk")
    account_lookup_field = ("pk", "account_pk")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            budget=self.budget,
            parent=self.account
        )
        return context

    def get_queryset(self):
        # The queryset will already be limited to SubAccount(s) that belong
        # to Budget(s) that are not in the Trash, because the @property
        # `account` only looks at active Budget(s).
        content_type = ContentType.objects.get_for_model(Account)
        return SubAccount.objects.filter(
            object_id=self.account.pk,
            content_type=content_type,
        )

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(
            updated_by=self.request.user,
            created_by=self.request.user,
            object_id=self.account.pk,
            content_type=ContentType.objects.get_for_model(Account),
            parent=self.account,
            budget=self.account.budget
        )
