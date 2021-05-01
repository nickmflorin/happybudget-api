from rest_framework import decorators, response, status, mixins

from greenbudget.app.common.mixins import NestedObjectViewMixin

from .models import Budget
from .permissions import BudgetObjPermission


class BudgetNestedMixin(NestedObjectViewMixin):
    """
    A mixin for views that extend off of a budget's detail endpoint.
    """
    budget_permission_classes = [BudgetObjPermission]
    view_name = "budget"

    def get_budget_queryset(self, request):
        return request.user.budgets.instance_of(Budget).active()


class TrashModelMixin(
    mixins.DestroyModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /<entity>/trash/
    (2) GET /<entity>/trash/<pk>/
    (3) PATCH /<entity>/trash/<pk>/restore/
    (4) DELETE /<entity>/trash/<pk>/
    """

    @decorators.action(detail=True, methods=["PATCH"])
    def restore(self, request, *args, **kwargs):
        """
        Moves the entity that is in the trash out of the trash to the active
        set of entities.

        PATCH /<entity>/trash/<pk>/restore/
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
