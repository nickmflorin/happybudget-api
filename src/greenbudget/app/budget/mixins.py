from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property

from rest_framework import decorators, response, status, mixins

from .models import Budget


class BudgetNestedMixin(object):
    """
    A mixin for views that extend off of a budget's detail endpoint.
    """
    @property
    def budget_lookup_field(self):
        raise NotImplementedError()

    @cached_property
    def budget(self):
        params = {
            self.budget_lookup_field[0]: (
                self.kwargs[self.budget_lookup_field[1]])
        }
        return get_object_or_404(
            self.request.user.budgets.instance_of(Budget).active(), **params)


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
