from rest_framework import viewsets, mixins, response, status, decorators

from greenbudget.app.account.models import AccountGroup
from greenbudget.app.account.serializers import AccountGroupSerializer

from .mixins import BudgetNestedMixin
from .serializers import BudgetSerializer


class BudgetAccountGroupViewSet(
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
    serializer_class = AccountGroupSerializer
    budget_lookup_field = ("pk", "budget_pk")

    def get_queryset(self):
        return AccountGroup.objects.filter(budget=self.budget)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(parent=self.budget)
        return context

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            budget=self.budget
        )


class GenericBudgetViewSet(viewsets.GenericViewSet):
    lookup_field = 'pk'
    serializer_class = BudgetSerializer
    ordering_fields = ['updated_at', 'name', 'created_at']
    search_fields = ['name']

    def get_object(self):
        instance = super().get_object()
        instance.raise_no_access(self.request.user)
        return instance


class UserBudgetViewSet(
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
    """

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            request=self.request,
            user=self.request.user,
        )
        return context

    def get_queryset(self):
        return self.request.user.budgets.active()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.to_trash()
        return response.Response(status=204)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class UserBudgetTrashViewSet(
    mixins.DestroyModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    GenericBudgetViewSet,
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /budgets/trash/
    (2) GET /budgets/trash/<pk>/
    (3) PATCH /budgets/trash/<pk>/restore/
    (4) DELETE /budgets/trash/<pk>/
    """

    def get_queryset(self):
        return self.request.user.budgets.inactive()

    @decorators.action(detail=True, methods=["PATCH"])
    def restore(self, request, *args, **kwargs):
        """
        Moves the :obj:`Budget`that is in the trash out of the trash
        to the main set of `obj:Budget`(s).

        PATCH /budgets/trash/<pk>/restore/
        """
        instance = self.get_object()
        instance.restore()
        return response.Response(
            self.serializer_class(instance).data,
            status=status.HTTP_201_CREATED
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)
