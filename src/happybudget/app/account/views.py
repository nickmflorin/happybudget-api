from django.contrib.contenttypes.models import ContentType
from django.db import models

from happybudget.app import views

from happybudget.app.account.models import Account
from happybudget.app.budget.permissions import BudgetObjPermission
from happybudget.app.budget.serializers import BudgetSerializer
from happybudget.app.budgeting.decorators import (
    register_bulk_operations, BulkAction, BulkDeleteAction)
from happybudget.app.group.models import Group
from happybudget.app.group.serializers import GroupSerializer
from happybudget.app.markup.models import Markup
from happybudget.app.markup.serializers import MarkupSerializer
from happybudget.app.subaccount.serializers import (
    BudgetSubAccountSerializer,
    TemplateSubAccountSerializer
)
from happybudget.app.subaccount.views import GenericSubAccountViewSet
from happybudget.app.template.permissions import TemplateObjPermission
from happybudget.app.template.serializers import TemplateSerializer

from .cache import (
    account_children_cache,
    account_groups_cache,
    account_markups_cache,
    account_instance_cache
)
from .mixins import AccountPublicNestedMixin
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
    views.CreateModelMixin,
    views.ListModelMixin,
    AccountPublicNestedMixin,
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
    views.CreateModelMixin,
    views.ListModelMixin,
    AccountPublicNestedMixin,
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
    views.CreateModelMixin,
    views.ListModelMixin,
    AccountPublicNestedMixin,
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
            child_serializer_cls=lambda context:
                context.view.child_serializer_cls,
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
    views.UpdateModelMixin,
    views.RetrieveModelMixin,
    views.DestroyModelMixin,
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
    queryset_cls = Account
    permission_classes = [
        BudgetObjPermission(
            get_budget=lambda obj: obj.budget,
            object_name='account',
            public=True,
            collaborator_can_destroy=True,
            is_object_applicable=lambda c: c.obj.domain == 'budget',
        ),
        TemplateObjPermission(
            get_budget=lambda obj: obj.budget,
            object_name='account',
            is_object_applicable=lambda c: c.obj.domain == 'template',
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
