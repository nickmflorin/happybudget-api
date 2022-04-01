from django.contrib.contenttypes.models import ContentType
from django.db import models

from rest_framework import response, status, decorators

from greenbudget.app import views, mixins, permissions
from greenbudget.app.account.serializers import (
    BudgetAccountSerializer, TemplateAccountSerializer)
from greenbudget.app.account.views import GenericAccountViewSet
from greenbudget.app.actual.models import Actual
from greenbudget.app.actual.serializers import (
    ActualSerializer, ActualOwnerSerializer)
from greenbudget.app.actual.views import GenericActualViewSet
from greenbudget.app.authentication.models import PublicToken
from greenbudget.app.authentication.serializers import PublicTokenSerializer
from greenbudget.app.budgeting.decorators import (
    register_bulk_operations, BulkAction, BulkDeleteAction)
from greenbudget.app.collaborator.models import Collaborator
from greenbudget.app.collaborator.permissions import (
    IsCollaborator, IsOwnerOrCollaboratingOwner, IsOwnerOrCollaborator)
from greenbudget.app.collaborator.serializers import CollaboratorSerializer
from greenbudget.app.fringe.models import Fringe
from greenbudget.app.fringe.serializers import FringeSerializer
from greenbudget.app.fringe.views import GenericFringeViewSet
from greenbudget.app.group.models import Group
from greenbudget.app.group.serializers import GroupSerializer
from greenbudget.app.markup.models import Markup
from greenbudget.app.markup.serializers import MarkupSerializer
from greenbudget.app.subaccount.models import BudgetSubAccount
from greenbudget.app.template.serializers import TemplateSerializer

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
from .permissions import MultipleBudgetPermission, BudgetOwnershipPermission
from .serializers import (
    BudgetSerializer,
    BudgetSimpleSerializer,
    BudgetPdfSerializer,
    BulkImportBudgetActualsSerializer
)


@views.filter_by_ids
@budget_markups_cache
class BudgetMarkupViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
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
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
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
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
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
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
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
    mixins.ListModelMixin,
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
        Overrides DRF's :obj:`mixins.ListModelMixin` so that the methodology
        (filtering, paginating, etc.) can be applied to multiple querysets
        at the same time.
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
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
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
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
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
    mixins.CreateModelMixin,
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
            'created_by': self.request.user
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
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
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
    permission_classes = [
        permissions.AND(
            permissions.OR(
                permissions.AND(
                    permissions.IsFullyAuthenticated(affects_after=True),
                    BudgetOwnershipPermission(affects_after=True),
                    MultipleBudgetPermission(
                        products="__any__",
                        is_view_applicable=lambda c: c.view.action in (
                            'create', 'duplicate'),
                    ),
                ),
                permissions.AND(
                    permissions.IsFullyAuthenticated(affects_after=True),
                    permissions.AND(
                        IsCollaborator,
                        permissions.IsNotViewAction('duplicate')
                    ),
                    is_view_applicable=False
                ),
                permissions.AND(
                    permissions.IsSafeRequestMethod,
                    permissions.IsPublic,
                    is_view_applicable=lambda c: c.view.action != "list"
                ),
                is_object_applicable=lambda c: c.obj.domain == 'budget',
            ),
            permissions.AND(
                permissions.IsFullyAuthenticated(affects_after=True),
                BudgetOwnershipPermission(affects_after=True),
                is_object_applicable=lambda c: c.obj.domain == 'template',
                is_view_applicable=False
            ),
            default=permissions.IsFullyAuthenticated
        )
    ]

    def get_queryset(self):
        base_cls = BaseBudget
        if self.action in ('pdf', 'list', 'bulk_import_actuals') \
                or self.in_bulk_entity('actuals'):
            base_cls = Budget
        if self.action == 'list':
            return base_cls.objects.filter(created_by=self.request.user)
        return base_cls.objects.all()

    @decorators.action(detail=True, methods=["GET"])
    def pdf(self, request, *args, **kwargs):
        serializer = BudgetPdfSerializer(self.instance)
        return response.Response(serializer.data, status=status.HTTP_200_OK)

    @decorators.action(detail=True, methods=["POST"])
    def duplicate(self, request, *args, **kwargs):
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

    @decorators.action(
        detail=True,
        methods=["PATCH"],
        url_path='bulk-import-actuals'
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
