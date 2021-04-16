from rest_framework import mixins, viewsets

from .models import Fringe
from .serializers import FringeSerializer


class FringesViewSet(
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /fringes/<pk>/
    (2) PATCH /fringes/<pk>/
    (3) DELETE /fringes/<pk>/
    """
    lookup_field = 'pk'
    serializer_class = FringeSerializer
    budget_lookup_field = ("pk", "budget_pk")

    def get_queryset(self):
        return Fringe.objects.filter(budget__trash=False)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
