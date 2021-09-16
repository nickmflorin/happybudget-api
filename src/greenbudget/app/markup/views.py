from django.utils.functional import cached_property
from rest_framework import viewsets, mixins

from .models import (
    Markup,
    BudgetAccountMarkup,
    BudgetSubAccountMarkup
)
from .serializers import (
    BudgetAccountMarkupSerializer, BudgetSubAccountMarkupSerializer)


class MarkupViewSet(
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """
    Viewset to handle requests to the following endpoints:

    (1) PATCH /markups/<pk>/
    (2) GET /markups/<pk>/
    (3) DELETE /markups/<pk>/
    """
    lookup_field = 'pk'

    @cached_property
    def instance_cls(self):
        instance = self.get_object()
        return type(instance)

    def get_serializer_class(self):
        mapping = {
            BudgetAccountMarkup: BudgetAccountMarkupSerializer,
            BudgetSubAccountMarkup: BudgetSubAccountMarkupSerializer,
        }
        return mapping[self.instance_cls]

    def get_queryset(self):
        return Markup.objects.filter(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
