from rest_framework import viewsets, mixins, decorators, response, status

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
    ActualNestedMixin,
    viewsets.GenericViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /actuals/<pk>/attachments/
    (2) DELETE /actuals/<pk>/attachments/pk/
    """
    actual_lookup_field = ("pk", "actual_pk")
    serializer_class = AttachmentSerializer

    def get_queryset(self):
        return self.actual.attachments.all()


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

    @decorators.action(
        detail=True, methods=["PATCH"], url_path='upload-attachment')
    def upload_attachment(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = UploadAttachmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attachment = serializer.save(created_by=request.user)
        instance.attachments.add(attachment)
        root_serializer_class = self.get_serializer_class()
        return response.Response(
            root_serializer_class(instance=instance).data,
            status=status.HTTP_200_OK
        )
