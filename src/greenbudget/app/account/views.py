from django.contrib.contenttypes.models import ContentType
from django.db import models

from greenbudget.app import views, mixins, permissions

from greenbudget.app.account.models import Account
from greenbudget.app.budget.serializers import BudgetSerializer
from greenbudget.app.budgeting.decorators import (
    register_bulk_operations, BulkAction, BulkDeleteAction)
from greenbudget.app.group.models import Group
from greenbudget.app.group.serializers import GroupSerializer
from greenbudget.app.markup.models import Markup
from greenbudget.app.markup.serializers import MarkupSerializer
from greenbudget.app.subaccount.serializers import (
    BudgetSubAccountSerializer,
    TemplateSubAccountSerializer
)
from greenbudget.app.subaccount.views import GenericSubAccountViewSet
from greenbudget.app.template.serializers import TemplateSerializer

from .cache import (
    account_children_cache,
    account_groups_cache,
    account_markups_cache,
    account_instance_cache
)
from .mixins import AccountSharedNestedMixin
from .permissions import (
    AccountOwnershipPermission,
    AccountProductPermission
)
from .serializers import (
    BudgetAccountDetailSerializer,
    TemplateAccountDetailSerializer,
    AccountSimpleSerializer,
    BudgetAccountSerializer,
    TemplateAccountSerializer
)


@views.filter_by_ids
@account_markups_cache
class AccountMarkupViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    AccountSharedNestedMixin,
    views.GenericViewSet,
):
    """
    Viewset to handle requests to the following endpoints:

    (1) POST /accounts/<pk>/markups/
    (2) GET /accounts/<pk>/markups/
    """
    serializer_class = MarkupSerializer

    def create_kwargs(self, serializer):
        return {**super().create_kwargs(serializer), **{
            'content_type': self.content_type,
            'object_id': self.object_id
        }}

    def get_queryset(self):
        return Markup.objects.filter(
            content_type=self.content_type,
            object_id=self.object_id
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(parent=self.instance)
        return context


@views.filter_by_ids
@account_groups_cache
class AccountGroupViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    AccountSharedNestedMixin,
    views.GenericViewSet,
):
    """
    Viewset to handle requests to the following endpoints:

    (1) POST /accounts/<pk>/groups/
    (2) GET /accounts/<pk>/groups/
    """
    serializer_class = GroupSerializer

    def get_queryset(self):
        return Group.objects.filter(
            content_type=self.content_type,
            object_id=self.object_id
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(parent=self.instance)
        return context


@views.filter_by_ids
@account_children_cache
class AccountChildrenViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    AccountSharedNestedMixin,
    GenericSubAccountViewSet,
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /accounts/<pk>/subaccounts
    (2) POST /accounts/<pk>/subaccounts
    """
    @property
    def child_instance_cls(self):
        return self.instance.child_instance_cls

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(parent=self.instance)
        return context

    def get_queryset(self):
        return self.child_instance_cls.objects.filter(
            object_id=self.object_id,
            content_type=self.content_type,
        ).order_with_groups()


class GenericAccountViewSet(views.GenericViewSet):
    ordering_fields = []
    search_fields = ['identifier', 'description']
    serializer_classes = (
        ({'is_simple': True}, AccountSimpleSerializer),
        ({'instance_cls.domain': 'template'}, [
            (
                {'action__in': ('create', 'partial_update', 'retrieve')},
                TemplateAccountDetailSerializer
            ),
            TemplateAccountSerializer
        ]),
        ({'instance_cls.domain': 'budget'}, [
            (
                {'action__in': ('create', 'partial_update', 'retrieve')},
                BudgetAccountDetailSerializer
            ),
            BudgetAccountSerializer
        ]),
    )


@register_bulk_operations(
    base_cls=lambda context: context.view.instance_cls,
    get_budget=lambda instance: instance.parent,
    budget_serializer=lambda context: context.view.budget_serializer,
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
            url_path='bulk-{action_name}-children',
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
            perform_create=lambda serializer, context: serializer.save(
                created_by=context.request.user,
                updated_by=context.request.user,
                parent=context.instance
            )
        )
    ]
)
@account_instance_cache
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
    (4) PATCH /accounts/<pk>/bulk-update-children/
    (5) PATCH /accounts/<pk>/bulk-create-children/
    """
    permission_classes = [
        permissions.OR(
            permissions.AND(
                permissions.IsFullyAuthenticated(affects_after=True),
                AccountOwnershipPermission(affects_after=True),
                AccountProductPermission(products="__any__")
            ),
            permissions.AND(
                permissions.IsShared(
                    get_permissioned_obj=lambda obj: obj.budget),
                permissions.IsSafeRequestMethod,
                is_object_applicable=lambda c: c.obj.domain == "budget"
            )
        )
    ]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(parent=self.instance.budget)
        return context

    @property
    def budget_serializer(self):
        return {
            'budget': BudgetSerializer,
            'template': TemplateSerializer
        }[self.instance_cls.domain]

    @property
    def child_instance_cls(self):
        return self.instance.child_instance_cls

    @property
    def child_serializer_cls(self):
        return {
            'budget': BudgetSubAccountSerializer,
            'template': TemplateSubAccountSerializer
        }[self.instance_cls.domain]

    def get_queryset(self):
        return Account.objects.all()
