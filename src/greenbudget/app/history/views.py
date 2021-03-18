from django.contrib.contenttypes.models import ContentType
from rest_framework import viewsets, mixins

from greenbudget.app.account.models import Account
from greenbudget.app.account.mixins import AccountNestedMixin
from greenbudget.app.budget.mixins import BudgetNestedMixin

from .models import FieldAlterationEvent
from .serializers import FieldAlterationEventSerializer


class GenericHistoryViewset(viewsets.GenericViewSet):
    lookup_field = 'pk'
    serializer_class = FieldAlterationEventSerializer
    ordering_fields = ['updated_at', 'created_at']
    search_fields = ['field']


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
        content_type = ContentType.objects.get_for_model(Account)
        return FieldAlterationEvent.objects.filter(
            object_id__in=[acct.pk for acct in self.budget.accounts.all()],
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
        content_type = ContentType.objects.get_for_model(Account)
        return FieldAlterationEvent.objects.filter(
            object_id=self.account.pk,
            content_type=content_type
        )


# class AccountCommentViewSet(
#     mixins.ListModelMixin,
#     AccountNestedMixin,
#     GenericFieldAlterationViewset
# ):
#     """
#     ViewSet to handle requests to the following endpoints:

#     (1) GET /accounts/<pk>/field-alterations/
#     """
#     account_lookup_field = ("pk", "account_pk")

#     def get_queryset(self):
#         content_type = ContentType.objects.get_for_model(Account)
#         return Comment.objects.filter(
#             object_id=self.account.pk,
#             content_type=content_type
#         )

#     def perform_create(self, serializer):
#         serializer.save(
#             user=self.request.user,
#             object_id=self.account.pk,
#             content_type=ContentType.objects.get_for_model(Account),
#             content_object=self.account
#         )


# class SubAccountCommentViewSet(
#     mixins.ListModelMixin,
#     SubAccountNestedMixin,
#     GenericFieldAlterationViewset
# ):
#     """
#     ViewSet to handle requests to the following endpoints:

#     (1) GET /subaccounts/<pk>/field-alterations/
#     """
#     subaccount_lookup_field = ("pk", "subaccount_pk")

#     def get_queryset(self):
#         content_type = ContentType.objects.get_for_model(SubAccount)
#         return Comment.objects.filter(
#             object_id=self.subaccount.pk,
#             content_type=content_type
#         )

#     def perform_create(self, serializer):
#         serializer.save(
#             user=self.request.user,
#             object_id=self.subaccount.pk,
#             content_type=ContentType.objects.get_for_model(SubAccount),
#             content_object=self.subaccount
#         )
