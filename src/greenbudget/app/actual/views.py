from django.contrib.contenttypes.models import ContentType
from rest_framework import viewsets, mixins

from greenbudget.app.account.mixins import AccountNestedMixin
from greenbudget.app.account.models import Account
from greenbudget.app.budget.mixins import BudgetNestedMixin
from greenbudget.app.subaccount.mixins import SubAccountNestedMixin
from greenbudget.app.subaccount.models import SubAccount

from .models import Actual
from .serializers import ActualSerializer


class GenericActualViewSet(viewsets.GenericViewSet):
    lookup_field = 'pk'
    serializer_class = ActualSerializer
    ordering_fields = ['updated_at', 'vendor', 'created_at']
    search_fields = ['vendor']

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            request=self.request,
            user=self.request.user,
        )
        return context

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(
            updated_by=self.request.user,
            created_by=self.request.user
        )


class ActualsViewSet(
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    GenericActualViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /actuals/<pk>/
    (2) PATCH /actuals/<pk>/
    (3) DELETE /actuals/<pk>/
    """

    def get_queryset(self):
        # TODO: Do we have to worry about filtering out actuals that belong
        # to a budget that might be in the trash?
        return Actual.objects.all()


class AccountActualsViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    AccountNestedMixin,
    GenericActualViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /accounts/<pk>/actuals/
    (2) POST /accounts/<pk>/actuals/
    """
    account_lookup_field = ("pk", "account_pk")

    def get_queryset(self):
        return self.account.actuals.all()

    def perform_create(self, serializer):
        serializer.save(
            updated_by=self.request.user,
            created_by=self.request.user,
            object_id=self.account.pk,
            content_type=ContentType.objects.get_for_model(Account),
            parent=self.account
        )


class SubAccountActualsViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    SubAccountNestedMixin,
    GenericActualViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /subaccounts/<pk>/actuals/
    (2) POST /subaccounts/<pk>/actuals/
    """
    subaccount_lookup_field = ("pk", "subaccount_pk")

    def get_queryset(self):
        return self.subaccount.actuals.all()

    def perform_create(self, serializer):
        serializer.save(
            updated_by=self.request.user,
            created_by=self.request.user,
            object_id=self.subaccount.pk,
            content_type=ContentType.objects.get_for_model(SubAccount),
            parent=self.subaccount
        )


class BudgetActualsViewSet(
    mixins.ListModelMixin,
    BudgetNestedMixin,
    GenericActualViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /budgets/<pk>/actuals/
    """
    budget_lookup_field = ("pk", "budget_pk")

    def get_queryset(self):
        # TODO: This is likely going to be an expensive set of queries, and
        # we should investigate if there are better ways to do this.
        actuals = []

        def add_subaccount_actuals(subaccount):
            actuals.extend(list(subaccount.actuals.all()))
            for subsubaccount in subaccount.subaccounts.all():
                add_subaccount_actuals(subsubaccount)

        for account in self.budget.accounts.all():
            actuals.extend(list(account.actuals.all()))
            for subaccount in account.subaccounts.all():
                add_subaccount_actuals(subaccount)

        return actuals
