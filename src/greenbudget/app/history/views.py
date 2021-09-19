from django.contrib.contenttypes.models import ContentType
from rest_framework import viewsets, mixins

from greenbudget.app.account.models import BudgetAccount
from greenbudget.app.account.mixins import AccountNestedMixin
from greenbudget.app.actual.models import Actual
from greenbudget.app.actual.mixins import ActualNestedMixin
from greenbudget.app.budget.mixins import BudgetNestedMixin
from greenbudget.app.subaccount.models import BudgetSubAccount
from greenbudget.app.subaccount.mixins import SubAccountNestedMixin

from .models import Event
from .serializers import EventPolymorphicSerializer


class GenericHistoryViewset(viewsets.GenericViewSet):
    lookup_field = 'pk'
    serializer_class = EventPolymorphicSerializer
    ordering_fields = ['updated_at', 'created_at']


class AccountsHistoryViewSet(
    mixins.ListModelMixin,
    BudgetNestedMixin,
    GenericHistoryViewset
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /budgets/<pk>/accounts/history/
    """
    budget_lookup_field = ("pk", "budget_pk")

    def get_queryset(self):
        content_type = ContentType.objects.get_for_model(BudgetAccount)
        return Event.objects.filter(
            object_id__in=[acct.pk for acct in self.budget.children.all()],
            content_type=content_type
        )


class AccountHistoryViewSet(
    mixins.ListModelMixin,
    AccountNestedMixin,
    GenericHistoryViewset
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /accounts/<pk>/history/
    """
    account_lookup_field = ("pk", "account_pk")

    def get_queryset(self):
        content_type = ContentType.objects.get_for_model(BudgetAccount)
        return Event.objects.filter(
            object_id=self.account.pk,
            content_type=content_type
        )


class AccountSubAccountsHistoryViewSet(
    mixins.ListModelMixin,
    AccountNestedMixin,
    GenericHistoryViewset
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /accounts/<pk>/subaccounts/history/
    """
    account_lookup_field = ("pk", "account_pk")

    def get_queryset(self):
        content_type = ContentType.objects.get_for_model(BudgetSubAccount)
        return Event.objects.filter(
            object_id__in=[acct.pk for acct in self.account.children.all()],
            content_type=content_type
        )


class SubAccountSubAccountsHistoryViewSet(
    mixins.ListModelMixin,
    SubAccountNestedMixin,
    GenericHistoryViewset
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /subaccounts/<pk>/subaccounts/history/
    """
    subaccount_lookup_field = ("pk", "subaccount_pk")

    def get_queryset(self):
        content_type = ContentType.objects.get_for_model(BudgetSubAccount)
        return Event.objects.filter(
            object_id__in=[
                acct.pk for acct in self.subaccount.children.all()],
            content_type=content_type
        )


class SubAccountHistoryViewSet(
    mixins.ListModelMixin,
    SubAccountNestedMixin,
    GenericHistoryViewset
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /subaccounts/<pk>/history/
    """
    subaccount_lookup_field = ("pk", "subaccount_pk")

    def get_queryset(self):
        content_type = ContentType.objects.get_for_model(BudgetSubAccount)
        return Event.objects.filter(
            object_id=self.subaccount.pk,
            content_type=content_type
        )


class ActualsHistoryViewSet(
    mixins.ListModelMixin,
    BudgetNestedMixin,
    GenericHistoryViewset
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /budgets/<pk>/actuals/history/
    """
    budget_lookup_field = ("pk", "budget_pk")

    def get_queryset(self):
        content_type = ContentType.objects.get_for_model(Actual)
        return Event.objects.filter(
            object_id__in=[actual.pk for actual in self.budget.actuals.all()],
            content_type=content_type
        )


class ActualHistoryViewSet(
    mixins.ListModelMixin,
    ActualNestedMixin,
    GenericHistoryViewset
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /actuals/<pk>/history/
    """
    actual_lookup_field = ("pk", "actual_pk")

    def get_queryset(self):
        content_type = ContentType.objects.get_for_model(Actual)
        return Event.objects.filter(
            object_id=self.actual.pk,
            content_type=content_type
        )
