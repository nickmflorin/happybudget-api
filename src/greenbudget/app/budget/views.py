from functools import cached_property
from django.contrib.contenttypes.models import ContentType
from django.db import models

from rest_framework import viewsets, mixins, response, status, decorators

from greenbudget.app.views import filter_by_ids, GenericViewSet

from greenbudget.app.account.models import BudgetAccount
from greenbudget.app.account.serializers import BudgetAccountSerializer
from greenbudget.app.account.views import GenericAccountViewSet
from greenbudget.app.actual.models import Actual
from greenbudget.app.actual.serializers import (
    ActualSerializer, OwnerTreeNodeSerializer)
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
from greenbudget.app.subaccount.serializers import SubAccountSimpleSerializer

from .cache import (
    budget_accounts_cache,
    budget_groups_cache,
    budget_markups_cache,
    budget_instance_cache,
    budget_actuals_cache,
    budget_fringes_cache,
    budget_actuals_owner_tree_cache
)
from .models import Budget
from .mixins import BudgetNestedMixin
from .serializers import (
    BudgetSerializer,
    BudgetSimpleSerializer,
    BudgetPdfSerializer
)


@filter_by_ids
@budget_markups_cache(get_instance_from_view=lambda view: view.budget.pk)
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
    serializer_class = MarkupSerializer
    budget_lookup_field = ("pk", "budget_pk")

    def get_queryset(self):
        return Markup.objects.filter(
            content_type=ContentType.objects.get_for_model(Budget),
            object_id=self.budget.pk
        )

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


@filter_by_ids
@budget_groups_cache(get_instance_from_view=lambda view: view.budget.pk)
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
    serializer_class = GroupSerializer
    budget_lookup_field = ("pk", "budget_pk")

    def get_queryset(self):
        return Group.objects.filter(
            content_type=ContentType.objects.get_for_model(type(self.budget)),
            object_id=self.budget.pk
        )

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
            content_type=ContentType.objects.get_for_model(type(self.budget)),
            object_id=self.budget.pk
        )


@filter_by_ids
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


@filter_by_ids
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


@filter_by_ids
@budget_actuals_owner_tree_cache(
    get_instance_from_view=lambda view: view.budget.pk)
class BudgetSubAccountViewSet(
    mixins.ListModelMixin,
    BudgetNestedMixin,
    viewsets.GenericViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /budgets/<pk>/subaccounts/

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

    def filter_tree_querysets(self, subaccount_qs, markup_qs):
        account_ct_id = ContentType.objects.get_for_model(BudgetAccount).pk
        budget_ct_id = ContentType.objects.get_for_model(Budget).pk
        subaccount_ct_id = ContentType.objects.get_for_model(BudgetSubAccount).pk  # noqa

        # Perform the search filter on each of the markup and sub account
        # querysets separately.
        searched_markup_qs = self.filter_queryset(markup_qs)
        searched_subaccount_qs = self.filter_queryset(subaccount_qs)

        def handle_nested_level(obj):
            qs = []
            search_path = []
            if obj in searched_subaccount_qs:
                # Here, the element matches the search criteria, so we add it
                # both to the overall queryset and to the search path.
                qs.append(obj)
                search_path.append(obj)

            # Note: These are not markups assigned to the SubAcount `obj`, but
            # are actually the Markup(s) that have the SubAccount `obj` as the
            # parent.
            for markup in markup_qs.filter(
                content_type_id=subaccount_ct_id,
                object_id=obj.id
            ).only('pk').all():
                if markup in searched_markup_qs:
                    qs.append(markup)
                    search_path.append(markup)
                    if markup.parent not in qs:
                        qs.append(markup.parent)

            for child in obj.children.only('pk').all():
                sub_qs, sub_path = handle_nested_level(child)
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

        # Since the Markup(s) at the Accounts level will not be nestled under
        # the SubAccount(s), if any of these meet the search criteria they have
        # to be added in separately because they will not be hit in the
        # below recursion.
        for child in markup_qs.filter(
                content_type_id__in=[budget_ct_id, account_ct_id]):
            if child in searched_markup_qs:
                overall_qs.append(child)
                overall_search_path.append(child)

        # Start at the top level of SubAccounts - use recursion.
        for child in subaccount_qs.filter(content_type_id=account_ct_id):
            qs_ext, path_ext = handle_nested_level(child)
            overall_qs.extend(qs_ext)
            overall_search_path.extend(path_ext)

        return overall_qs, overall_search_path

    @decorators.action(methods=["GET"], detail=False, url_path='owner-tree')
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
        account_ct_id = ContentType.objects.get_for_model(BudgetAccount).pk
        budget_ct_id = ContentType.objects.get_for_model(Budget).pk

        sub_account_qs = BudgetSubAccount.objects \
            .exclude(models.Q(identifier=None) & models.Q(description=None)) \
            .filter_by_budget(self.budget) \
            .only('pk')

        markup_qs = Markup.objects \
            .exclude(models.Q(identifier=None) & models.Q(description=None)) \
            .filter_by_budget(self.budget) \
            .only('pk')

        overall_qs, search_path = self.filter_tree_querysets(
            sub_account_qs,
            markup_qs
        )

        qs = self.paginate_queryset(overall_qs)
        top_level = [
            obj for obj in qs
            if (isinstance(obj, Markup)
                and obj.content_type_id in [budget_ct_id, account_ct_id])
            or obj.content_type_id == account_ct_id
        ]
        non_top_level = [
            obj for obj in qs
            if obj not in top_level
        ]
        data = OwnerTreeNodeSerializer(
            top_level,
            subset=non_top_level,
            search_path=search_path,
            many=True
        ).data
        return self.get_paginated_response(data)


@filter_by_ids
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
    budget_lookup_field = ("pk", "budget_pk")
    instance_cls = Budget

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            parent=self.budget,
            budget_context=True
        )
        return context

    def get_queryset(self):
        return BudgetAccount.objects.filter(parent=self.budget).all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(
            updated_by=self.request.user,
            created_by=self.request.user,
            parent=self.budget
        )


class GenericBudgetViewSet(GenericViewSet):
    lookup_field = 'pk'
    ordering_fields = ['updated_at', 'name', 'created_at']
    search_fields = ['name']
    serializer_classes = (
        ({'action': 'list'}, BudgetSimpleSerializer),
        BudgetSerializer
    )

    @property
    def serializer_class(self):
        return self.get_serializer_class()


@register_bulk_operations(
    base_cls=Budget,
    get_budget=lambda instance: instance,
    # Since the Budget is the entity being updated, it will already be included
    # in the response by default.  We do not want to double include it.
    include_budget_in_response=False,
    child_context_indicator='budget_context',
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
    @cached_property
    def instance(self):
        return self.get_object()

    def get_queryset(self):
        return Budget.objects.filter(created_by=self.request.user).all()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

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
