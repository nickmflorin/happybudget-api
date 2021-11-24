from rest_framework import mixins

from greenbudget.app.views import GenericViewSet

from .models import Fringe
from .serializers import FringeSerializer, FringeDetailSerializer


class GenericFringeViewSet(GenericViewSet):
    lookup_field = 'pk'
    ordering_fields = []
    search_fields = ['name']
    serializer_class = FringeSerializer
    serializer_classes = [
        ({'action__in': ['partial_update', 'create', 'retrieve']},
            FringeDetailSerializer),
    ]


class FringesViewSet(
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    GenericFringeViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /fringes/<pk>/
    (2) PATCH /fringes/<pk>/
    (3) DELETE /fringes/<pk>/
    """
    budget_lookup_field = ("pk", "budget_pk")

    def get_queryset(self):
        return Fringe.objects.all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
