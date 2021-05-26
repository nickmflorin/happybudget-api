from django.http import HttpResponse
from rest_framework import viewsets, mixins, response, status, decorators

from greenbudget.lib.rest_framework_utils.pagination import Pagination

from greenbudget.app.account.models import BudgetAccount
from greenbudget.app.account.serializers import (
    BudgetAccountSerializer,
    create_bulk_create_accounts_serializer,
    create_bulk_update_accounts_serializer
)
from greenbudget.app.actual.serializers import BulkUpdateActualsSerializer
from greenbudget.app.common.serializers import EntitySerializer
from greenbudget.app.common.signals import disable_budget_tracking
from greenbudget.app.fringe.serializers import (
    FringeSerializer,
    BulkCreateFringesSerializer,
    BulkUpdateFringesSerializer
)
from greenbudget.app.group.models import BudgetAccountGroup
from greenbudget.app.group.serializers import BudgetAccountGroupSerializer
from greenbudget.app.subaccount.models import BudgetSubAccount

from .models import Budget
from .mixins import BudgetNestedMixin, TrashModelMixin
from .serializers import (
    BudgetSerializer, EntitySerializerWithChildren, BudgetSimpleSerializer)


class LineItemTreePagination(Pagination):
    """
    Paginatation class that includes the active search path in the paginated
    response.  See documentation of LineItemTreeViewSet.list for more context.
    """
    page_size = 20
    page_query_param = 'page'
    page_size_query_param = 'page_size'

    def paginate_queryset(self, queryset, request, view=None):
        # Allow the pagination to be completely turned off on a per-request
        # basis.
        if 'no_pagination' in request.query_params:
            self._no_pagination = True
            return queryset
        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        if getattr(self, '_no_pagination', False) is True:
            return response.Response(
                OrderedDict([
                    ('count', len(data)),
                    ('next', None),
                    ('previous', None),
                    ('data', data),
                ])
            )
        return response.Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('data', data)
        ]))


class LineItemViewSet(
    mixins.ListModelMixin,
    BudgetNestedMixin,
    viewsets.GenericViewSet
):
    """
    Viewset to handle requests to the following endpoints:

    (1) GET /budgets/<pk>/items/
    """
    serializer_class = EntitySerializer
    budget_lookup_field = ("pk", "budget_pk")
    search_fields = ['identifier', 'description']

    def list(self, request, *args, **kwargs):
        qs1 = self.filter_queryset(self.budget.accounts.all())
        qs2 = self.filter_queryset(
            BudgetSubAccount.objects.filter(budget=self.budget))
        qs = self.paginate_queryset(list(qs1) + list(qs2))
        serializer = EntitySerializer(qs, many=True)
        return self.get_paginated_response(serializer.data)


class LineItemTreeViewSet(
    mixins.ListModelMixin,
    BudgetNestedMixin,
    viewsets.GenericViewSet
):
    """
    Viewset to handle requests to the following endpoints:

    (1) GET /budgets/<pk>/items/tree/
    """
    budget_lookup_field = ("pk", "budget_pk")
    search_fields = ['identifier', 'description']

    def filter_tree_querysets(self, account_qs, subaccount_qs):
        def filter_children_qs(obj, search_qs):
            qs = []
            active_path = []
            for subaccount in obj.subaccounts.all():
                sub_qs, sub_path = filter_children_qs(subaccount, search_qs)
                if len(sub_qs) != 0:
                    if obj not in qs:
                        qs.append(obj)

                    qs.extend(sub_qs)
            return qs
        overall_qs = []
        active_search_path = []
        for account in self.budget.accounts.all():
            if account in account_qs:
                overall_qs.append(account)
                # The account is in the filtered queryset, so it is on the
                # active search path.
                active_search_path.append(account)
            qs_ext, path_ext = filter_children_qs(account, subaccount_qs)
            overall_qs.extend(qs_ext)
            active_search_path.extend(path_ext)
        return overall_qs, active_search_path

    def list(self, request, *args, **kwargs):
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
        call this the "Active Search Path".  Since each node of the tree will
        only be present in the tree at most 1 time, this "Active Search Path"
        is a unique set of nodes, in this case:

        ['foo.barb.bara', 'foob.bara']
        """
        qs1 = self.filter_queryset(self.budget.accounts.all())
        qs2 = self.filter_queryset(
            BudgetSubAccount.objects.filter(budget=self.budget))
        overall_qs, active_search_path = self.filter_tree_querysets(qs1, qs2)

        # Note: Since we are applying the pagination before the TreeSerializer,
        # the `count` in the paginated response will not be the number of
        # top-level accounts but will instead be the number of overall items
        # returned for all levels of the tree.
        qs = self.paginate_queryset(overall_qs)
        accounts = [obj for obj in qs if isinstance(obj, BudgetAccount)]
        subaccounts = [obj for obj in qs if isinstance(obj, BudgetSubAccount)]
        data = [
            EntitySerializerWithChildren(account, subset=subaccounts).data
            for account in accounts
        ]
        return self.get_paginated_response(
            data, active_search_path=active_search_path)


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
        context.update(parent=self.budget)
        return context

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            parent=self.budget
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
        context.update(budget=self.budget)
        return context

    def get_queryset(self):
        return self.budget.fringes.all()

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user,
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
        return self.request.user.budgets.instance_of(Budget).active()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.to_trash()
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_bulk_accounts_change(self, serializer_cls, request):
        instance = self.get_object()
        serializer = serializer_cls(
            instance=instance,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        with disable_budget_tracking():
            data = serializer.save(updated_by=request.user)
        instance.mark_updated()
        return data

    @decorators.action(
        detail=True, url_path='bulk-update-accounts', methods=["PATCH"])
    def bulk_update_accounts(self, request, *args, **kwargs):
        serializer_cls = create_bulk_update_accounts_serializer(BudgetAccount)
        instance = self.perform_bulk_accounts_change(serializer_cls, request)
        return response.Response(
            self.serializer_class(instance).data,
            status=status.HTTP_200_OK
        )

    @decorators.action(
        detail=True, url_path='bulk-create-accounts', methods=["PATCH"])
    def bulk_create_budget_accounts(self, request, *args, **kwargs):
        serializer_cls = create_bulk_create_accounts_serializer(BudgetAccount)
        accounts = self.perform_bulk_accounts_change(serializer_cls, request)
        return response.Response(
            {'data': BudgetAccountSerializer(accounts, many=True).data},
            status=status.HTTP_201_CREATED
        )

    @decorators.action(
        detail=True, url_path='bulk-update-actuals', methods=["PATCH"])
    def bulk_update_actuals(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = BulkUpdateActualsSerializer(
            instance=instance,
            data=request.data,
            partial=True,
            context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        with disable_budget_tracking():
            data = serializer.save(updated_by=request.user)
        instance.mark_updated()
        return response.Response(
            self.serializer_class(data).data,
            status=status.HTTP_200_OK
        )

    @decorators.action(
        detail=True, url_path='bulk-update-fringes', methods=["PATCH"])
    def bulk_update_fringes(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = BulkUpdateFringesSerializer(
            instance=instance,
            data=request.data,
            partial=True,
            context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        with disable_budget_tracking():
            data = serializer.save(updated_by=request.user)
        instance.mark_updated()
        return response.Response(
            self.serializer_class(data).data,
            status=status.HTTP_200_OK
        )

    @decorators.action(
        detail=True, url_path='bulk-create-fringes', methods=["PATCH"])
    def bulk_create_fringes(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = BulkCreateFringesSerializer(
            instance=instance,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        with disable_budget_tracking():
            fringes = serializer.save(updated_by=request.user)
        instance.mark_updated()
        return response.Response(
            {'data': FringeSerializer(fringes, many=True).data},
            status=status.HTTP_201_CREATED
        )

    @decorators.action(detail=True, methods=["GET"])
    def pdf(self, request, *args, **kwargs):
        instance = self.get_object()
        pdf = instance.to_pdf()
        return HttpResponse(pdf.getvalue(), content_type='application/pdf')

    @decorators.action(detail=True, methods=["POST"])
    def duplicate(self, request, *args, **kwargs):
        instance = self.get_object()
        duplicated = Budget.objects.create(
            original=instance, created_by=request.user)
        return response.Response(
            self.serializer_class(duplicated).data,
            status=status.HTTP_201_CREATED
        )


class BudgetTrashViewSet(TrashModelMixin, GenericBudgetViewSet):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /budgets/trash/
    (2) GET /budgets/trash/<pk>/
    (3) PATCH /budgets/trash/<pk>/restore/
    (4) DELETE /budgets/trash/<pk>/
    """

    def get_queryset(self):
        return self.request.user.budgets.instance_of(Budget).inactive()
