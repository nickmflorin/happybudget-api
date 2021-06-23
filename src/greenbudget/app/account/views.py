from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.functional import cached_property

from rest_framework import viewsets, mixins, permissions

from greenbudget.app.account.models import Account
from greenbudget.app.account.mixins import AccountNestedMixin
from greenbudget.app.budget.decorators import (
    register_bulk_updating_and_creating, BulkAction)
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
)
from greenbudget.app.subaccount.views import GenericSubAccountViewSet

from .models import BudgetAccount, TemplateAccount
from .permissions import AccountObjPermission
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
        context.update(
            parent=self.account,
            account_context=True
        )
        return context

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            object_id=self.account.pk,
            content_type=ContentType.objects.get_for_model(type(self.account)),
            parent=self.account
        )


class AccountSubAccountViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    AccountNestedMixin,
    GenericSubAccountViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /accounts/<pk>/subaccounts
    (2) POST /accounts/<pk>/subaccounts
    """
    account_lookup_field = ("pk", "account_pk")

    @cached_property
    def instance_cls(self):
        return type(self.account)

    @property
    def child_instance_cls(self):
        if self.instance_cls is BudgetAccount:
            return BudgetSubAccount
        return TemplateSubAccount

    def get_serializer_class(self):
        if self.child_instance_cls is TemplateSubAccount:
            return TemplateSubAccountSerializer
        return BudgetSubAccountSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            parent=self.account,
            account_context=True
        )
        return context

    def get_queryset(self):
        content_type = ContentType.objects.get_for_model(type(self.account))
        return self.child_instance_cls.objects.filter(
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
            content_type=ContentType.objects.get_for_model(type(self.account)),
            parent=self.account,
            budget=self.account.budget
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


@register_bulk_updating_and_creating(
    base_cls=lambda context: context.view.instance_cls,
    child_context=lambda context: {
        'budget': context.instance.budget,
        'account_context': True
    },
    actions=[
        BulkAction(
            url_path='bulk-{action_name}-subaccounts',
            child_cls=lambda context: context.view.child_instance_cls,
            child_serializer_cls=lambda context: context.view.child_serializer_cls,  # noqa
            filter_qs=lambda context: models.Q(
                budget=context.instance.budget,
                object_id=context.instance.pk,
                content_type=ContentType.objects.get_for_model(
                    context.view.instance_cls)
            ),
            perform_update=lambda serializer, context: serializer.save(
                updated_by=context.request.user
            ),
            perform_create=lambda serializer, context: serializer.save(  # noqa
                created_by=context.request.user,
                updated_by=context.request.user,
                parent=context.instance,
                budget=context.instance.budget
            )
        )
    ]
)
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
    permission_classes = (
        permissions.IsAuthenticated,
        AccountObjPermission,
    )

    @cached_property
    def instance_cls(self):
        instance = self.get_object()
        return type(instance)

    @property
    def child_instance_cls(self):
        if self.instance_cls is BudgetAccount:
            return BudgetSubAccount
        return TemplateSubAccount

    @property
    def child_serializer_cls(self):
        if self.child_instance_cls is BudgetSubAccount:
            return BudgetSubAccountSerializer
        return TemplateSubAccountSerializer

    def get_queryset(self):
        return Account.objects.filter(budget__trash=False)

    def get_serializer_class(self):
        if self.instance_cls is TemplateAccount:
            return TemplateAccountSerializer
        return BudgetAccountSerializer

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
