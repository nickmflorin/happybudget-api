from rest_framework import viewsets, mixins, response, status

from greenbudget.app.authentication.permissions import DEFAULT_PERMISSIONS
from greenbudget.app.io.serializers import (
    UploadAttachmentSerializer, AttachmentSerializer)

from .mixins import ActualNestedMixin
from .models import Actual, ActualType
from .permissions import ActualObjPermission
from .serializers import ActualSerializer, ActualTypeSerializer


class ActualTypeViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
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
    viewsets.GenericViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /actuals/<pk>/attachments/
    (2) DELETE /actuals/<pk>/attachments/pk/
    (3) POST /actuals/<pk>/attachments/
    """
    actual_lookup_field = ("pk", "actual_pk")
    serializer_class = AttachmentSerializer
    lookup_field = "pk"

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
    permission_classes = DEFAULT_PERMISSIONS + (ActualObjPermission, )

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def get_queryset(self):
        return Actual.objects.all()
