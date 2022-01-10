from greenbudget.app import views, mixins
from greenbudget.app.io.views import GenericAttachmentViewSet

from .mixins import ActualNestedMixin
from .models import Actual, ActualType
from .serializers import (
    ActualSerializer,
    ActualTypeSerializer,
    ActualDetailSerializer
)


class ActualTypeViewSet(mixins.ListModelMixin, views.GenericViewSet):
    """
    Viewset to handle requests to the following endpoints:

    (1) GET /actuals/types/
    """
    serializer_class = ActualTypeSerializer

    def get_queryset(self):
        return ActualType.objects.all()


class ActualAttachmentViewSet(
    ActualNestedMixin,
    GenericAttachmentViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /actuals/<pk>/attachments/
    (2) DELETE /actuals/<pk>/attachments/pk/
    (3) POST /actuals/<pk>/attachments/
    """
    pass


class GenericActualViewSet(views.GenericViewSet):
    ordering_fields = []
    search_fields = ['description']
    serializer_class = ActualSerializer
    serializer_classes = [
        ({'action__in': ['partial_update', 'create', 'retrieve']},
            ActualDetailSerializer),
    ]


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

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(budget=self.instance.budget)
        return context

    def get_queryset(self):
        return Actual.objects.filter(created_by=self.request.user)
