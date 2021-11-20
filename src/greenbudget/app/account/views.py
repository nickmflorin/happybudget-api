from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.functional import cached_property

from rest_framework import viewsets, mixins

from greenbudget.app.views import filter_by_ids

from greenbudget.app.account.models import Account
from greenbudget.app.account.mixins import AccountNestedMixin
from greenbudget.app.authentication.permissions import DEFAULT_PERMISSIONS
from greenbudget.app.budgeting.decorators import (
    register_bulk_operations, BulkAction, BulkDeleteAction)
from greenbudget.app.group.models import Group
from greenbudget.app.group.serializers import GroupSerializer
from greenbudget.app.markup.models import Markup
from greenbudget.app.markup.serializers import MarkupSerializer
from greenbudget.app.subaccount.models import (
    BudgetSubAccount, TemplateSubAccount)
from greenbudget.app.subaccount.serializers import (
    BudgetSubAccountSerializer,
    TemplateSubAccountSerializer,
    SubAccountSimpleSerializer
)
from greenbudget.app.subaccount.views import GenericSubAccountViewSet

from .cache import (
    account_subaccounts_cache,
    account_groups_cache,
    account_markups_cache,
    account_instance_cache
)
from .models import BudgetAccount, TemplateAccount
from .permissions import AccountObjPermission
from .serializers import (
    BudgetAccountDetailSerializer,
    TemplateAccountDetailSerializer
)


@filter_by_ids
@account_markups_cache(get_instance_from_view=lambda view: view.account.pk)
class AccountMarkupViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    AccountNestedMixin,
    viewsets.GenericViewSet
):
    """
    Viewset to handle requests to the following endpoints:

    (1) POST /accounts/<pk>/markups/
    (2) GET /accounts/<pk>/markups/
    """
    lookup_field = 'pk'
    account_lookup_field = ("pk", "account_pk")
    serializer_class = MarkupSerializer

    def get_queryset(self):
        return Markup.objects.filter(
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
            updated_by=self.request.user,
            object_id=self.account.pk,
            content_type=ContentType.objects.get_for_model(type(self.account)),
            parent=self.account
        )


@filter_by_ids
@account_groups_cache(get_instance_from_view=lambda view: view.account.pk)
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
    serializer_class = GroupSerializer

    def get_queryset(self):
        return Group.objects.filter(
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
            updated_by=self.request.user,
            object_id=self.account.pk,
            content_type=ContentType.objects.get_for_model(type(self.account)),
            parent=self.account
        )


@filter_by_ids
@account_subaccounts_cache(get_instance_from_view=lambda view: view.account.pk)
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

    @property
    def is_simple(self):
        return 'simple' in self.request.query_params

    @cached_property
    def instance_cls(self):
        return type(self.account)

    @property
    def child_instance_cls(self):
        if self.instance_cls is BudgetAccount:
            return BudgetSubAccount
        return TemplateSubAccount

    def get_serializer_class(self):
        if self.is_simple:
            return SubAccountSimpleSerializer
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
            parent=self.account
        )


class GenericAccountViewSet(viewsets.GenericViewSet):
    lookup_field = 'pk'
    ordering_fields = ['updated_at', 'created_at']
    search_fields = ['identifier', 'description']

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            request=self.request,
            user=self.request.user,
        )
        return context


@register_bulk_operations(
    base_cls=lambda context: context.view.instance_cls,
    child_context_indicator='account_context',
    get_budget=lambda instance: instance.parent,
    child_context=lambda context: {"parent": context.instance},
    actions=[
        BulkDeleteAction(
            url_path='bulk-{action_name}-markups',
            child_cls=Markup,
            filter_qs=lambda context: models.Q(
                content_type=ContentType.objects.get_for_model(context.instance),
                object_id=context.instance.pk
            ),
        ),
        BulkAction(
            url_path='bulk-{action_name}-subaccounts',
            child_cls=lambda context: context.view.child_instance_cls,
            child_serializer_cls=lambda context: context.view.child_serializer_cls,  # noqa
            filter_qs=lambda context: models.Q(
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
                parent=context.instance
            )
        )
    ]
)
@account_instance_cache(get_instance_from_view=lambda view: view.instance.pk)
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
    permission_classes = DEFAULT_PERMISSIONS + (AccountObjPermission, )

    @cached_property
    def instance(self):
        return self.get_object()

    @property
    def instance_cls(self):
        return type(self.instance)

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
        return Account.objects.all()

    def get_serializer_class(self):
        if self.instance_cls is TemplateAccount:
            return TemplateAccountDetailSerializer
        return BudgetAccountDetailSerializer

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
