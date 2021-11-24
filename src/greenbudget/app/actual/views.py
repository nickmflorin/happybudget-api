from rest_framework import response, status

from greenbudget.app import views, mixins
from greenbudget.app.io.serializers import (
    UploadAttachmentSerializer, AttachmentSerializer)

from .mixins import ActualNestedMixin
from .models import Actual, ActualType
from .permissions import ActualObjPermission
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
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    mixins.CreateModelMixin,
    ActualNestedMixin,
    views.GenericViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /actuals/<pk>/attachments/
    (2) DELETE /actuals/<pk>/attachments/pk/
    (3) POST /actuals/<pk>/attachments/
    """
    serializer_class = AttachmentSerializer

    def get_queryset(self):
        return self.actual.attachments.all()

    def create(self, request, *args, **kwargs):
        serializer = UploadAttachmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attachment = serializer.save(created_by=request.user)
        self.actual.attachments.add(attachment)
        root_serializer_class = self.get_serializer_class()
        return response.Response(
            root_serializer_class(instance=attachment).data,
            status=status.HTTP_200_OK
        )


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
    extra_permission_classes = (ActualObjPermission, )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(budget=self.instance.budget)
        return context

    def get_queryset(self):
        return Actual.objects.all()
