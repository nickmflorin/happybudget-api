from django.contrib.contenttypes.models import ContentType
from django.db import models

from rest_framework import response, status, decorators

from greenbudget.app import views, mixins
from greenbudget.app.account.models import BudgetAccount
from greenbudget.app.account.serializers import BudgetAccountSerializer
from greenbudget.app.account.views import GenericAccountViewSet
from greenbudget.app.actual.models import Actual
from greenbudget.app.actual.serializers import (
    ActualSerializer, ActualOwnerSerializer)
from greenbudget.app.actual.views import GenericActualViewSet
from greenbudget.app.budgeting.decorators import (
    register_bulk_operations, BulkAction, BulkDeleteAction)
from greenbudget.app.fringe.models import Fringe
from greenbudget.app.fringe.serializers import FringeSerializer
from greenbudget.app.fringe.views import GenericFringeViewSet
from greenbudget.app.group.models import Group
from greenbudget.app.group.serializers import GroupSerializer
from greenbudget.app.markup.models import Markup
from greenbudget.app.markup.serializers import MarkupSerializer
from greenbudget.app.subaccount.models import BudgetSubAccount

from .cache import (
    budget_accounts_cache,
    budget_groups_cache,
    budget_markups_cache,
    budget_instance_cache,
    budget_actuals_cache,
    budget_fringes_cache,
    budget_actuals_owners_cache
)
from .models import Budget
from .mixins import BudgetNestedMixin
from .serializers import (
    BudgetSerializer,
    BudgetSimpleSerializer,
    BudgetPdfSerializer
)


@views.filter_by_ids
@budget_markups_cache(get_instance_from_view=lambda view: view.budget.pk)
class BudgetMarkupViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    BudgetNestedMixin,
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
            content_type=ContentType.objects.get_for_model(Budget),
            object_id=self.budget.pk
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(parent=self.budget)
        return context


@views.filter_by_ids
@budget_groups_cache(get_instance_from_view=lambda view: view.budget.pk)
class BudgetGroupViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    BudgetNestedMixin,
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
@budget_actuals_cache(get_instance_from_view=lambda view: view.budget.pk)
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


@budget_actuals_owners_cache(
    get_instance_from_view=lambda view: view.budget.pk)
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
@budget_fringes_cache(get_instance_from_view=lambda view: view.budget.pk)
class BudgetFringeViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    BudgetNestedMixin,
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
@budget_accounts_cache(get_instance_from_view=lambda view: view.budget.pk)
class BudgetAccountViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    BudgetNestedMixin,
    GenericAccountViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /budgets/<pk>/accounts/
    (2) POST /budgets/<pk>/accounts/
    """
    instance_cls = Budget

    def create_kwargs(self, serializer):
        return {**super().create_kwargs(serializer), **{'parent': self.budget}}

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(parent=self.budget)
        return context

    def get_queryset(self):
        return BudgetAccount.objects.filter(parent=self.budget).all()


class GenericBudgetViewSet(views.GenericViewSet):
    ordering_fields = ['updated_at', 'name', 'created_at']
    search_fields = ['name']
    serializer_class = BudgetSerializer
    serializer_classes = [
        ({'action': 'list'}, BudgetSimpleSerializer)
    ]


@register_bulk_operations(
    base_cls=Budget,
    get_budget=lambda instance: instance,
    # Since the Budget is the entity being updated, it will already be included
    # in the response by default.  We do not want to double include it.
    include_budget_in_response=False,
    child_context=lambda context: {"parent": context.instance},
    perform_update=lambda serializer, context: serializer.save(
        updated_by=context.request.user
    ),
    actions=[
        BulkAction(
            url_path='bulk-{action_name}-accounts',
            child_cls=BudgetAccount,
            child_serializer_cls=BudgetAccountSerializer,
            filter_qs=lambda context: models.Q(parent=context.instance),
            perform_create=lambda serializer, context: serializer.save(
                created_by=context.request.user,
                updated_by=context.request.user,
                parent=context.instance
            ),
        ),
        BulkDeleteAction(
            url_path='bulk-{action_name}-markups',
            child_cls=Markup,
            filter_qs=lambda context: models.Q(
                content_type=ContentType.objects.get_for_model(Budget),
                object_id=context.instance.pk
            ),
        ),
        BulkAction(
            url_path='bulk-{action_name}-actuals',
            child_cls=Actual,
            child_serializer_cls=ActualSerializer,
            filter_qs=lambda context: models.Q(budget=context.instance),
            perform_create=lambda serializer, context: serializer.save(
                created_by=context.request.user,
                updated_by=context.request.user,
                budget=context.instance
            ),
        ),
        BulkAction(
            url_path='bulk-{action_name}-fringes',
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
@budget_instance_cache(get_instance_from_view=lambda view: view.instance.pk)
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
    (6) PATCH /budgets/<pk>/bulk-update-accounts/
    (7) PATCH /budgets/<pk>/bulk-create-accounts/
    (8) PATCH /budgets/<pk>/bulk-update-actuals/
    (9) PATCH /budgets/<pk>/bulk-update-fringes/
    (10) PATCH /budgets/<pk>/bulk-create-fringes/
    (11) GET /budgets/<pk>/pdf/
    (12) POST /budgets/<pk>/duplicate/
    """

    def get_queryset(self):
        return Budget.objects.filter(created_by=self.request.user).all()

    @decorators.action(detail=True, methods=["GET"])
    def pdf(self, request, *args, **kwargs):
        serializer = BudgetPdfSerializer(self.instance)
        return response.Response(serializer.data, status=status.HTTP_200_OK)

    @decorators.action(detail=True, methods=["POST"])
    def duplicate(self, request, *args, **kwargs):
        duplicated = type(self.instance).objects.duplicate(
            self.instance, request.user)
        return response.Response(
            self.serializer_class(duplicated).data,
            status=status.HTTP_201_CREATED
        )
