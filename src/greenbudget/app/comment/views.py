from django.contrib.contenttypes.models import ContentType
from rest_framework import viewsets, mixins

from greenbudget.app.account.models import Account
from greenbudget.app.account.mixins import AccountNestedMixin
from greenbudget.app.budget.models import Budget
from greenbudget.app.budget.mixins import BudgetNestedMixin
from greenbudget.app.subaccount.models import SubAccount
from greenbudget.app.subaccount.mixins import SubAccountNestedMixin

from .models import Comment
from .serializers import CommentSerializer


class GenericCommentViewSet(viewsets.GenericViewSet):
    lookup_field = 'pk'
    serializer_class = CommentSerializer
    ordering_fields = ['updated_at', 'created_at']
    search_fields = []


class CommentViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericCommentViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /comments/<pk>/
    (2) PATCH /comments/<pk>/
    (3) DELETE /comments/<pk>/
    """

    def get_queryset(self):
        # TODO: How do we filter by comments that belong a budget or
        # accounts/subaccounts that are in a budget that is not in the trash?
        return Comment.objects.all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class BudgetCommentViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    BudgetNestedMixin,
    GenericCommentViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /budgets/<pk>/comments/
    (2) POST /budgets/<pk>/comments/
    """

    def get_queryset(self):
        content_type = ContentType.objects.get_for_model(Comment)
        return Comment.objects.filter(
            object_id=self.budget.pk,
            content_type=content_type
        )

    def perform_create(self, serializer):
        serializer.save(
            updated_by=self.request.user,
            created_by=self.request.user,
            object_id=self.budget.pk,
            content_type=ContentType.objects.get_for_model(Budget),
            content_object=self.budget
        )


class AccountCommentViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    AccountNestedMixin,
    GenericCommentViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /accounts/<pk>/comments/
    (2) POST /accounts/<pk>/comments/
    """

    def get_queryset(self):
        content_type = ContentType.objects.get_for_model(Account)
        return Comment.objects.filter(
            object_id=self.account.pk,
            content_type=content_type
        )

    def perform_create(self, serializer):
        serializer.save(
            updated_by=self.request.user,
            created_by=self.request.user,
            object_id=self.account.pk,
            content_type=ContentType.objects.get_for_model(Account),
            content_object=self.account
        )


class SubAccountCommentViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    SubAccountNestedMixin,
    GenericCommentViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /subaccounts/<pk>/comments/
    (2) POST /subaccounts/<pk>/comments/
    """

    def get_queryset(self):
        content_type = ContentType.objects.get_for_model(SubAccount)
        return Comment.objects.filter(
            object_id=self.subaccount.pk,
            content_type=content_type
        )

    def perform_create(self, serializer):
        serializer.save(
            updated_by=self.request.user,
            created_by=self.request.user,
            object_id=self.subaccount.pk,
            content_type=ContentType.objects.get_for_model(SubAccount),
            content_object=self.subaccount
        )
