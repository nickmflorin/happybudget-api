from django.utils.functional import cached_property

from greenbudget.app import views, mixins

from .models import Fringe
from .serializers import FringeSerializer, FringeDetailSerializer


class GenericFringeViewSet(views.GenericViewSet):
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
    @cached_property
    def instance(self):
        return self.get_object()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(budget=self.instance.budget)
        return context

    def get_queryset(self):
        return Fringe.objects.all()
