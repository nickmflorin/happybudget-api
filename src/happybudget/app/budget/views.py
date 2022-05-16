from django.contrib.contenttypes.models import ContentType
from django.db import models

from rest_framework import response, status

from happybudget.app import views, permissions, exceptions
from happybudget.app.account.serializers import (
    BudgetAccountSerializer, TemplateAccountSerializer)
from happybudget.app.account.views import GenericAccountViewSet
from happybudget.app.actual.models import Actual
from happybudget.app.actual.serializers import (
    ActualSerializer, ActualOwnerSerializer)
from happybudget.app.actual.views import GenericActualViewSet
from happybudget.app.authentication.models import PublicToken
from happybudget.app.authentication.serializers import PublicTokenSerializer
from happybudget.app.budgeting.decorators import (
    register_bulk_operations, BulkAction, BulkDeleteAction)
from happybudget.app.collaborator.models import Collaborator
from happybudget.app.collaborator.permissions import (
    IsOwnerOrCollaboratingOwner, IsOwnerOrCollaborator)
from happybudget.app.collaborator.serializers import CollaboratorSerializer
from happybudget.app.fringe.models import Fringe
from happybudget.app.fringe.serializers import FringeSerializer
from happybudget.app.fringe.views import GenericFringeViewSet
from happybudget.app.group.models import Group
from happybudget.app.group.serializers import GroupSerializer
from happybudget.app.markup.models import Markup
from happybudget.app.markup.serializers import MarkupSerializer
from happybudget.app.subaccount.models import BudgetSubAccount
from happybudget.app.template.permissions import TemplateObjPermission
from happybudget.app.template.serializers import TemplateSerializer

from .cache import (
    budget_children_cache,
    budget_groups_cache,
    budget_markups_cache,
    budget_instance_cache,
    budget_actuals_cache,
    budget_fringes_cache,
    budget_actuals_owners_cache
)
from .models import Budget, BaseBudget
from .mixins import BudgetNestedMixin, BaseBudgetPublicNestedMixin
from .permissions import MultipleBudgetPermission, BudgetObjPermission
from .serializers import (
    BudgetSerializer,
    BudgetSimpleSerializer,
    BudgetPdfSerializer,
    BulkImportBudgetActualsSerializer
)


@views.filter_by_ids
@budget_markups_cache
class BudgetMarkupViewSet(
    views.CreateModelMixin,
    views.ListModelMixin,
    BaseBudgetPublicNestedMixin,
    views.GenericViewSet
):
    """
    Viewset to handle requests to the following endpoints:

    (1) POST /budgets/<pk>/markups/
    (2) GET /budgets/<pk>/markups/
    """
    serializer_class = MarkupSerializer

    def create_kwargs(self, serializer):
        return {**super().create_kwargs(serializer), **{'parent': self.budget}}

    def get_queryset(self):
        return Markup.objects.filter(
            content_type=self.content_type,
            object_id=self.budget.pk
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(parent=self.budget)
        return context


@views.filter_by_ids
@budget_groups_cache
class BudgetGroupViewSet(
    views.CreateModelMixin,
    views.ListModelMixin,
    BaseBudgetPublicNestedMixin,
    views.GenericViewSet
):
    """
    Viewset to handle requests to the following endpoints:

    (1) POST /budgets/<pk>/groups/
    (2) GET /budgets/<pk>/groups/
    """
    serializer_class = GroupSerializer

    def create_kwargs(self, serializer):
        return {**super().create_kwargs(serializer), **{
            'content_type': self.content_type,
            'object_id': self.budget.pk
        }}

    def get_queryset(self):
        return Group.objects.filter(
            content_type=self.content_type,
            object_id=self.budget.pk
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(parent=self.budget)
        return context


@views.filter_by_ids
@budget_actuals_cache
class BudgetActualsViewSet(
    views.ListModelMixin,
    views.CreateModelMixin,
    BudgetNestedMixin,
    GenericActualViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /budgets/<pk>/actuals/
    (2) POST /budgets/<pk>/actuals/
    """
    def create_kwargs(self, serializer):
        return {
            **super().create_kwargs(serializer),
            **{'budget': self.budget}
        }

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(budget=self.budget)
        return context

    def get_queryset(self):
        return Actual.objects.filter(budget=self.budget)


class BudgetCollaboratorsViewSet(
    views.ListModelMixin,
    views.CreateModelMixin,
    BudgetNestedMixin,
    views.GenericViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /budgets/<pk>/collaborators/
    (2) POST /budgets/<pk>/collaborators/
    """
    serializer_class = CollaboratorSerializer
    budget_permission_classes = [
        permissions.IsFullyAuthenticated(affects_after=True),
        IsOwnerOrCollaboratingOwner(is_object_applicable=lambda c:
            permissions.request_is_write_method(c.request)),
        IsOwnerOrCollaborator(is_object_applicable=lambda c:
            permissions.request_is_safe_method(c.request))
    ]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(budget=self.budget)
        return context

    def create_kwargs(self, serializer):
        return {**super().create_kwargs(serializer), **{
            'content_type': self.content_type,
            'object_id': self.budget.pk
        }}

    def get_queryset(self):
        return Collaborator.objects.filter(
            content_type=self.content_type,
            object_id=self.budget.pk
        )


@budget_actuals_owners_cache
class BudgetActualsOwnersViewSet(
    views.ListModelMixin,
    BudgetNestedMixin,
    views.GenericViewSet
):
    serializer_class = ActualOwnerSerializer
    search_fields = ['identifier', 'description']

    def get_queryset(self):
        return BudgetSubAccount.objects \
            .exclude(models.Q(identifier=None) & models.Q(description=None)) \
            .filter_by_budget(budget=self.budget)

    def get_markup_queryset(self):
        return Markup.objects \
            .exclude(models.Q(identifier=None) & models.Q(description=None)) \
            .filter_by_budget(self.budget)

    def list(self, request, *args, **kwargs):
        """
        Overrides DRF's :obj:`views.ListModelMixin` so that the
        methodology (filtering, paginating, etc.) can be applied to multiple
        querysets at the same time.
        """
        sub_account_qs = self.filter_queryset(self.get_queryset())
        markup_qs = self.filter_queryset(self.get_markup_queryset())
        page = self.paginate_queryset(list(sub_account_qs) + list(markup_qs))
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(
            list(sub_account_qs) + list(markup_qs), many=True)
        return response.Response(serializer.data, status=status.HTTP_200_OK)


@views.filter_by_ids
@budget_fringes_cache
class BudgetFringeViewSet(
    views.CreateModelMixin,
    views.ListModelMixin,
    BaseBudgetPublicNestedMixin,
    GenericFringeViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /budgets/<pk>/fringes/
    (2) POST /budgets/<pk>/fringes/
    """
    def create_kwargs(self, serializer):
        return {**super().create_kwargs(serializer), **{'budget': self.budget}}

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(budget=self.budget)
        return context

    def get_queryset(self):
        return self.budget.fringes.all()


@views.filter_by_ids
@budget_children_cache
class BudgetChildrenViewSet(
    views.CreateModelMixin,
    views.ListModelMixin,
    BaseBudgetPublicNestedMixin,
    GenericAccountViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /budgets/<pk>/children/
    (2) POST /budgets/<pk>/children/
    """
    def create_kwargs(self, serializer):
        return {**super().create_kwargs(serializer), **{'parent': self.budget}}

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(parent=self.budget)
        return context

    @property
    def child_instance_cls(self):
        return self.instance.child_instance_cls

    def get_queryset(self):
        return self.child_instance_cls.objects \
            .filter(parent=self.instance).order_with_groups()


class BudgetPublicTokenViewSet(
    views.CreateModelMixin,
    BudgetNestedMixin,
    views.GenericViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) POST /budgets/<pk>/public-token/
    """
    serializer_class = PublicTokenSerializer

    def create_kwargs(self, serializer):
        return {**super().create_kwargs(serializer), **{
            'content_type': self.content_type,
            'object_id': self.budget.pk,
            'created_by': self.request.user,
        }}

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(instance=self.budget)
        return context

    def get_queryset(self):
        return PublicToken.objects.filter(
            created_by=self.request.user,
            object_id=self.budget.pk,
            content_type=self.content_type
        )


class GenericBudgetViewSet(views.GenericViewSet):
    ordering_fields = ['updated_at', 'name', 'created_at']
    search_fields = ['name']
    serializer_class = BudgetSerializer
    serializer_classes = (
        ({'action': 'list'}, BudgetSimpleSerializer),
        ({'action': 'create'}, BudgetSerializer),
        ({'instance_cls.domain': 'template'}, TemplateSerializer)
    )


class CollaboratingBudgetViewSet(views.ListModelMixin, GenericBudgetViewSet):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /budgets/collaborating/
    """
    def get_queryset(self):
        return self.request.user.collaborating_budgets


class AcrhivedBudgetViewSet(views.ListModelMixin, GenericBudgetViewSet):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /budgets/archived/
    """
    def get_queryset(self):
        return Budget.objects.filter(archived=True, created_by=self.request.user)


@register_bulk_operations(
    base_cls=BaseBudget,
    get_budget=lambda instance: instance,
    # Since the Budget is the entity being updated, it will already be included
    # in the response by default.  We do not want to double include it.
    include_budget_in_response=False,
    budget_serializer=lambda context: {
        'budget': BudgetSerializer,
        'template': TemplateSerializer
    }[context.instance.domain],
    child_context=lambda context: {"parent": context.instance},
    perform_update=lambda serializer, context: serializer.save(
        updated_by=context.request.user
    ),
    actions=[
        BulkAction(
            entity='children',
            url_path='bulk-{action_name}-{entity}',
            child_cls=lambda context: context.instance.account_cls,
            child_serializer_cls=lambda context: {
                'template': TemplateAccountSerializer,
                'budget': BudgetAccountSerializer
            }[context.instance.domain],
            filter_qs=lambda context: models.Q(parent=context.instance),
            perform_create=lambda serializer, context: serializer.save(
                created_by=context.request.user,
                updated_by=context.request.user,
                parent=context.instance
            ),
        ),
        BulkDeleteAction(
            entity='markups',
            url_path='bulk-{action_name}-{entity}',
            child_cls=Markup,
            filter_qs=lambda context: models.Q(
                content_type=ContentType.objects.get_for_model(
                    type(context.instance)),
                object_id=context.instance.pk
            ),
        ),
        BulkAction(
            entity='actuals',
            url_path='bulk-{action_name}-{entity}',
            child_cls=Actual,
            child_serializer_cls=ActualSerializer,
            disabled=lambda context: context.instance.domain != "budget",

            filter_qs=lambda context: models.Q(budget=context.instance),
            perform_create=lambda serializer, context: serializer.save(
                created_by=context.request.user,
                updated_by=context.request.user,
                budget=context.instance
            ),
        ),
        BulkAction(
            entity='fringes',
            url_path='bulk-{action_name}-{entity}',
            child_cls=Fringe,
            child_serializer_cls=FringeSerializer,
            filter_qs=lambda context: models.Q(budget=context.instance),
            perform_create=lambda serializer, context: serializer.save(
                created_by=context.request.user,
                updated_by=context.request.user,
                budget=context.instance
            ),
        )
    ]
)
@budget_instance_cache
class BudgetViewSet(
    views.CreateModelMixin,
    views.UpdateModelMixin,
    views.RetrieveModelMixin,
    views.ListModelMixin,
    views.DestroyModelMixin,
    GenericBudgetViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /budgets/
    (2) POST /budgets/
    (3) GET /budgets/<pk>/
    (4) PATCH /budgets/<pk>/
    (5) DELETE /budgets/<pk>/
    (6) PATCH /budgets/<pk>/bulk-update-children/
    (7) PATCH /budgets/<pk>/bulk-create-children/
    (8) PATCH /budgets/<pk>/bulk-delete-children/
    (9) PATCH /budgets/<pk>/bulk-update-actuals/
    (10) PATCH /budgets/<pk>/bulk-create-actuals/
    (11) PATCH /budgets/<pk>/bulk-delete-actuals/
    (12) PATCH /budgets/<pk>/bulk-update-fringes/
    (13) PATCH /budgets/<pk>/bulk-create-fringes/
    (14) PATCH /budgets/<pk>/bulk-delete-fringes/
    (15) PATCH /budgets/<pk>/bulk-delete-markups/
    (16) GET /budgets/<pk>/pdf/
    (17) POST /budgets/<pk>/duplicate/
    (18) PATCH /budgets/<pk>/bulk-import-actuals/
    """
    permission_classes = [permissions.OR(
        permissions.AND(
            permissions.IsViewAction('list', affects_after=True),
            permissions.IsFullyAuthenticated(priority=True),
            priority=lambda c: c.view.action == 'list',
        ),
        permissions.AND(
            permissions.IsViewAction('create', 'duplicate', affects_after=True),
            permissions.AND(
                permissions.IsFullyAuthenticated(affects_after=True),
                permissions.IsOwner(object_name='budget', affects_after=True),
                MultipleBudgetPermission(
                    is_object_applicable=lambda c: c.obj.domain == 'budget'
                ),
                priority=True
            ),
            priority=lambda c: c.view.action in ('create', 'duplicate'),
        ),
        permissions.AND(
            permissions.IsNotViewAction(
                'list', 'create', 'duplicate', 'bulk_import_actuals',
                affects_after=True
            ),
            permissions.AND(
                BudgetObjPermission(
                    # Collaborators are not allowed to delete or duplicate the
                    # budget, only view and edit it's contents.
                    collaborator_can_destroy=False,
                    restricted_collaborator_actions=('partial_update'),
                    # A user should be able to delete a Budget even if it is
                    # not permissioned due to the User's billing status.
                    product_can_destroy=True,
                    public=True,
                    is_object_applicable=lambda c: c.obj.domain == 'budget'
                ),
                TemplateObjPermission(
                    is_object_applicable=lambda c: c.obj.domain == 'template',
                ),
                priority=True,
                default=permissions.IsFullyAuthenticated
            ),
            priority=lambda c:
            c.view.action not in (
                'list', 'create', 'duplicate', 'bulk_import_actuals')
        ),
        permissions.AND(
            permissions.IsViewAction('bulk_import_actuals'),
            BudgetObjPermission(
                # Only the collaborator with owner privileges can import
                # actuals.
                collaborator_access_types=(Collaborator.ACCESS_TYPES.owner,),
                public=False,
                priority=True
            ),
            priority=lambda c:
            c.view.action == 'bulk_import_actuals',
            is_object_applicable=lambda c: c.obj.domain == 'budget',
        )
    )]

    def get_queryset(self):
        base_cls = BaseBudget
        if self.action in ('pdf', 'list', 'bulk_import_actuals') \
                or self.in_bulk_entity('actuals'):
            # Actuals and PDF are only relevant for the budget domain.  The
            # template domain for list actions is handled by a separate view.
            base_cls = Budget
        qs = base_cls.objects
        if self.action == 'list':
            qs = qs.filter(created_by=self.request.user)
            # Archived Budget(s) are handled by a separate view.
            if base_cls is Budget:
                qs = qs.filter(archived=False)
        return qs.all()

    @views.action(detail=True, methods=["GET"])
    def pdf(self, request, *args, **kwargs):
        serializer = BudgetPdfSerializer(self.instance)
        return response.Response(serializer.data, status=status.HTTP_200_OK)

    @views.action(detail=True, methods=["POST"])
    def duplicate(self, request, *args, **kwargs):
        # We do not want to allow duplicating archived budgets, but we cannot
        # perform this filter in the `get_queryset` method because duplication
        # applies for both Templates and Budgets, but archiving does not apply
        # for Templates - so the base_cls will not appropriately handle the
        # filter.
        if getattr(self.instance, 'archived', False) is True:
            raise exceptions.BadRequest(
                'Duplicating archived budgets is not permitted.')
        duplicated = type(self.instance).objects.duplicate(
            self.instance, request.user)
        serializer_class = self.get_serializer_class()
        return response.Response(
            serializer_class(
                duplicated,
                context=self.get_serializer_context()
            ).data,
            status=status.HTTP_201_CREATED
        )

    @views.action(
        detail=True,
        methods=["PATCH"],
        url_path='bulk-import-actuals',
        hidden=lambda s: not s.PLAID_ENABLED
    )
    def bulk_import_actuals(self, request, *args, **kwargs):
        serializer = BulkImportBudgetActualsSerializer(
            instance=self.instance,
            data=request.data,
            context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        budget, actuals = serializer.save()
        return response.Response({
            'parent': BudgetSerializer(
                budget,
                context=self.get_serializer_context()
            ).data,
            'children': ActualSerializer(actuals, many=True).data
        }, status=status.HTTP_200_OK)
