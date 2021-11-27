from rest_framework import response, generics, status

from greenbudget.app import views, mixins
from .serializers import (
    TempImageSerializer, TempFileSerializer, AttachmentSerializer,
    UploadAttachmentSerializer)


class TempUploadView(generics.GenericAPIView):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        file_url = serializer.save()
        return response.Response({'fileUrl': file_url})


class TempUploadImageView(TempUploadView):
    serializer_class = TempImageSerializer


class TempUploadFileView(TempUploadView):
    serializer_class = TempFileSerializer


class GenericAttachmentViewSet(
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    mixins.CreateModelMixin,
    views.GenericViewSet
):
    serializer_class = AttachmentSerializer

    def get_queryset(self):
        return self.instance.attachments.all()

    def create(self, request, *args, **kwargs):
        serializer = UploadAttachmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attachment = serializer.save(created_by=request.user)
        self.instance.attachments.add(attachment)
        root_serializer_class = self.get_serializer_class()
        return response.Response(
            root_serializer_class(instance=attachment).data,
            status=status.HTTP_200_OK
        )
