from rest_framework import viewsets, mixins

from .models import Actual
from .serializers import ActualSerializer


class GenericActualViewSet(viewsets.GenericViewSet):
    lookup_field = 'pk'
    serializer_class = ActualSerializer
    ordering_fields = ['updated_at', 'created_at']
    search_fields = ['description']

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(request=self.request)
        return context


class ActualsViewSet(
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    GenericActualViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /actuals/<pk>/
    (2) PATCH /actuals/<pk>/
    (3) DELETE /actuals/<pk>/
    """

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def get_queryset(self):
        return Actual.objects.all()
