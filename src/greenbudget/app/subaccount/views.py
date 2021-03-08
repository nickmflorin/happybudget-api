from django.contrib.contenttypes.models import ContentType
from rest_framework import viewsets, mixins

from greenbudget.app.account.models import Account
from greenbudget.app.account.mixins import AccountNestedMixin

from .mixins import SubAccountNestedMixin
from .models import SubAccount
from .serializers import SubAccountSerializer


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

    def get_queryset(self):
        # TODO: How do we filter for only subaccounts whose budget is not
        # in the trash?  Because the parent can be both a budget and a
        # subaccount.
        return SubAccount.objects.all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(
            updated_by=self.request.user,
            created_by=self.request.user
        )


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
        context.update(parent=self.subaccount)
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

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(
            updated_by=self.request.user,
            created_by=self.request.user,
            object_id=self.subaccount.pk,
            content_type=ContentType.objects.get_for_model(SubAccount),
            parent=self.subaccount
        )


class AccountSubAccountViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    AccountNestedMixin,
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
            parent=self.account
        )
