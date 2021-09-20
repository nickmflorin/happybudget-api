from django.contrib.contenttypes.models import ContentType
from django.db import models

from rest_framework import viewsets, mixins, response, status, decorators

from greenbudget.app.account.models import BudgetAccount
from greenbudget.app.account.serializers import BudgetAccountSerializer
from greenbudget.app.account.views import GenericAccountViewSet
from greenbudget.app.actual.models import Actual
from greenbudget.app.actual.serializers import ActualSerializer
from greenbudget.app.actual.views import GenericActualViewSet
from greenbudget.app.fringe.models import Fringe
from greenbudget.app.fringe.serializers import FringeSerializer
from greenbudget.app.group.models import BudgetAccountGroup
from greenbudget.app.group.serializers import BudgetAccountGroupSerializer
from greenbudget.app.markup.models import BudgetAccountMarkup
from greenbudget.app.markup.serializers import BudgetAccountMarkupSerializer
from greenbudget.app.subaccount.models import BudgetSubAccount
from greenbudget.app.subaccount.serializers import (
    SubAccountSimpleSerializer, SubAccountTreeNodeSerializer)

from .decorators import register_all_bulk_operations, BulkAction
from .models import Budget
from .mixins import BudgetNestedMixin
from .serializers import BudgetSerializer, BudgetSimpleSerializer
from .pdf_serializers import BudgetPdfSerializer


class BudgetMarkupViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    BudgetNestedMixin,
    viewsets.GenericViewSet
):
    """
    Viewset to handle requests to the following endpoints:

    (1) POST /budgets/<pk>/markups/
    (2) GET /budgets/<pk>/markups/
    """
    lookup_field = 'pk'
    serializer_class = BudgetAccountMarkupSerializer
    budget_lookup_field = ("pk", "budget_pk")

    def get_queryset(self):
        return BudgetAccountMarkup.objects.filter(parent=self.budget)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            parent=self.budget,
            budget_context=True
        )
        return context

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user,
            parent=self.budget
        )


class BudgetGroupViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    BudgetNestedMixin,
    viewsets.GenericViewSet
):
    """
    Viewset to handle requests to the following endpoints:

    (1) POST /budgets/<pk>/groups/
    (2) GET /budgets/<pk>/groups/
    """
    lookup_field = 'pk'
    serializer_class = BudgetAccountGroupSerializer
    budget_lookup_field = ("pk", "budget_pk")

    def get_queryset(self):
        return BudgetAccountGroup.objects.filter(parent=self.budget)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            parent=self.budget,
            budget_context=True
        )
        return context

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user,
            parent=self.budget
        )


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
    budget_lookup_field = ("pk", "budget_pk")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            budget=self.budget,
            budget_context=True
        )
        return context

    def get_queryset(self):
        return Actual.objects.filter(budget=self.budget)

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user,
            budget=self.budget
        )


class BudgetFringeViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    BudgetNestedMixin,
    viewsets.GenericViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /budgets/<pk>/fringes/
    (2) POST /budgets/<pk>/fringes/
    """
    lookup_field = 'pk'
    serializer_class = FringeSerializer
    budget_lookup_field = ("pk", "budget_pk")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            budget=self.budget,
            budget_context=True
        )
        return context

    def get_queryset(self):
        return self.budget.fringes.all()

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user,
            budget=self.budget
        )


class BudgetSubAccountViewSet(
    mixins.ListModelMixin,
    BudgetNestedMixin,
    GenericAccountViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /budgets/<pk>/subaccounts/
    (2) GET /budgets/<pk>/subaccounts/tree/

    Note that any given :obj:`greenbudget.app.subaccount.BudgetSubAccount`
    is not a direct child of the :obj:`greenbudget.app.budget.Budget` but
    an indirect child, either through a
    :obj:`greenbudget.app.account.BudgetAccount` or another
    :obj:`greenbudget.app.subaccount.BudgetSubAccount`.

    Budget -> Account -> SubAccount (1st Level) -> SubAccount (2nd Level) ...

    This means that this endpoint returns ALL of the
    :obj:`greenbudget.app.subaccount.BudgetSubAccount`(s) associated with the
    :obj:`greenbudget.app.budget.Budget` - at any level of the tree.

    This is primarily used for establishing relationships between an
    :obj:`greenbudget.app.actual.Actual` and the
    :obj:`greenbudget.app.subaccount.BudgetSubAccount` by the FE.  It does
    not apply to templates.
    """
    budget_lookup_field = ("pk", "budget_pk")
    serializer_class = SubAccountSimpleSerializer
    search_fields = ['identifier', 'description']

    def get_queryset(self):
        return BudgetSubAccount.objects \
            .exclude(models.Q(identifier=None) & models.Q(description=None)) \
            .filter_by_budget(budget=self.budget)

    def filter_tree_querysets(self, top_level_qs, searched_qs):
        def handle_nested_level(obj):
            qs = []
            search_path = []
            if obj in searched_qs:
                # Here, the element matches the search criteria, so we add it
                # both to the overall queryset and to the search path.
                qs.append(obj)
                search_path.append(obj)

            for subaccount in obj.subaccounts.all():
                sub_qs, sub_path = handle_nested_level(subaccount)
                if len(sub_qs) != 0:
                    if obj not in qs:
                        # Here, we do not add the element to the search path
                        # because if it met the search criteria, it would have
                        # already been added in the block before the loop:
                        # >>> if obj in primary:  search_path.append(obj).
                        # The element here is only added because it has children
                        # that match the search criteria, so it is needed to
                        # maintain the shape of the tree.
                        qs.append(obj)
                    qs.extend(sub_qs)
                    search_path.extend(sub_path)
            return qs, search_path

        overall_qs = []
        overall_search_path = []

        for subaccount in top_level_qs.all():
            qs_ext, path_ext = handle_nested_level(subaccount)
            overall_qs.extend(qs_ext)
            overall_search_path.extend(path_ext)
        return overall_qs, overall_search_path

    @decorators.action(methods=["GET"], detail=False, url_path='tree')
    def tree(self, request, *args, **kwargs):
        """
        Implements custom tree searching & pagination.

        The problem that this method attempts to solve is how to return
        results filtered for a search criteria when those results are in
        a tree.

        Consider the following tree:

        -- foo
        ---- bard
        ---- barb
        ------ bara
        -- foob
        ---- bara
        -- fooc
        ---- barc

        When we are searching for "bara", we need to filter the tree such
        that the results for "bara" are shown, but also maintain the shape
        of the tree.  This will result in a tree like this:

        -- foo
        ---- barb
        ------ bara
        -- foob
        ---- bara

        However, we need to include information in the response about
        specifically what points in the tree match the search criteria.  We
        call this the "Search Path".  Since each node of the tree will only be
        present in the tree at most 1 time, this "Search Path" is a unique set
        of nodes, in this case:

        ['foo.barb.bara', 'foob.bara']
        """
        top_level_qs = BudgetSubAccount.objects \
            .filter(content_type=ContentType.objects.get_for_model(
                BudgetAccount)) \
            .exclude(models.Q(identifier=None) & models.Q(description=None)) \
            .filter_by_budget(self.budget)

        queryset = self.filter_queryset(self.get_queryset())
        overall_qs, search_path = self.filter_tree_querysets(
            top_level_qs, queryset)

        qs = self.paginate_queryset(overall_qs)

        top_level_subaccounts = [
            obj for obj in qs
            if obj.content_type == ContentType.objects.get_for_model(BudgetAccount)  # noqa
        ]
        non_top_level_subaccounts = [
            obj for obj in qs
            if obj.content_type != ContentType.objects.get_for_model(BudgetAccount)  # noqa
        ]
        data = SubAccountTreeNodeSerializer(
            top_level_subaccounts,
            subset=non_top_level_subaccounts,
            search_path=search_path,
            many=True
        ).data
        return self.get_paginated_response(data)


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
    budget_lookup_field = ("pk", "budget_pk")
    serializer_class = BudgetAccountSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            budget=self.budget,
            budget_context=True
        )
        return context

    def get_queryset(self):
        return BudgetAccount.objects.filter(budget=self.budget).all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(
            updated_by=self.request.user,
            created_by=self.request.user,
            budget=self.budget
        )


class GenericBudgetViewSet(viewsets.GenericViewSet):
    lookup_field = 'pk'
    ordering_fields = ['updated_at', 'name', 'created_at']
    search_fields = ['name']

    def get_serializer_class(self):
        if self.action == 'list':
            return BudgetSimpleSerializer
        return BudgetSerializer

    @property
    def serializer_class(self):
        return self.get_serializer_class()


@register_all_bulk_operations(
    base_cls=Budget,
    filter_qs=lambda context: models.Q(budget=context.instance),
    get_budget=lambda instance: instance,
    # Since the Budget is the entity being updated, it will already be included
    # in the response by default.  We do not want to double include it.
    include_budget_in_response=False,
    child_context_indicator='budget_context',
    perform_update=lambda serializer, context: serializer.save(  # noqa
        updated_by=context.request.user
    ),
    perform_create=lambda serializer, context: serializer.save(  # noqa
        created_by=context.request.user,
        updated_by=context.request.user,
        budget=context.instance
    ),
    actions=[
        BulkAction(
            url_path='bulk-{action_name}-accounts',
            child_cls=BudgetAccount,
            child_serializer_cls=BudgetAccountSerializer
        ),
        BulkAction(
            url_path='bulk-{action_name}-actuals',
            child_cls=Actual,
            child_serializer_cls=ActualSerializer,
        ),
        BulkAction(
            url_path='bulk-{action_name}-fringes',
            child_cls=Fringe,
            child_serializer_cls=FringeSerializer,
        )
    ]
)
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

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            request=self.request,
            user=self.request.user,
        )
        return context

    def get_queryset(self):
        return Budget.objects.filter(created_by=self.request.user).all()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @decorators.action(detail=True, methods=["GET"])
    def pdf(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = BudgetPdfSerializer(instance)
        return response.Response(serializer.data, status=status.HTTP_200_OK)

    @decorators.action(detail=True, methods=["POST"])
    def duplicate(self, request, *args, **kwargs):
        instance = self.get_object()
        duplicated = instance.duplicate(request.user)
        return response.Response(
            self.serializer_class(duplicated).data,
            status=status.HTTP_201_CREATED
        )
