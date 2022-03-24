from rest_framework import response, generics, status

from greenbudget.app import views, mixins
from .serializers import (
    TempImageSerializer, TempFileSerializer, AttachmentSerializer,
    UploadAttachmentsSerializer)


class TempUploadView(generics.GenericAPIView):
    def post(self, request, *args, **kwargs):
        # pylint: disable=not-callable
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
        serializer = UploadAttachmentsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attachments = serializer.save(created_by=request.user)
        self.instance.attachments.add(*attachments)
        root_serializer_class = self.get_serializer_class()
        return response.Response(
            {'data': [root_serializer_class(a).data for a in attachments]},
            status=status.HTTP_200_OK
        )
