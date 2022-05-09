from rest_framework import response, generics, status

from happybudget.app import views

from .models import Attachment
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
    views.ListModelMixin,
    views.DestroyModelMixin,
    views.CreateModelMixin,
    views.GenericViewSet
):
    serializer_class = AttachmentSerializer

    def get_permissioned_queryset(self):
        # Implemented such that the view can determine whether or not to raise
        # permission errors related to the Attachment belonging to the incorrect
        # instance or a 404 due to the Attachment not existing at all.
        return Attachment.objects.all()

    def get_queryset(self):
        """
        Due to the M2M relationships that Attachments will have in relation to
        another model, the DELETE endpoints for deleting an Attachment will be
        of the following form:

        DELETE /<model_name>/<instance_pk>/attachments/<pk>/

        The problem with this is that when sending a request to the DELETE
        endpoint, object level permission checks will not be performed on the
        nested instance (the instance associated with `instance_pk`) because
        we do not need to access the nested instance in order to perform a
        DELETE operation.

        This means that if we were to return the queryset as the following:

        >>> return Attachment.objects.all()

        Then the nested object level permissions on the instance the Attachment
        is associated with will (dictated by `instance_pk`) not be performed,
        and it is possible that a :obj:`User` can access an an :obj:`Attachment`
        belonging to an instance that they are not permissioned to access.

        So we need to return the queryset as the following:

        >>> return self.instance.attachments.all()

        This will properly trigger the nested object level permission checks
        on the nested object, `self.instance`, associated with `instance_pk`,
        such that the :obj:`User` cannot access an :obj:`Attachment` that
        belongs to another instance they are not permissioned to see.

        However, this means that if the Attachment does not belong
        to the correct instance, but exists, the response will be a 404, when
        it is more desirable that a permission error is raised.

        To do this we also define the `get_perissioned_queryset` method, which
        will allow the :obj:`happybudget.app.views.GenericViewSet` to raise
        object level permissions errors on the :obj:`Attachment` itself instead
        of a 404 when the :obj:`Attachment` does in fact exist but does not
        belong to the correct instance.  If the :obj:`Attachment` does not
        exist at all, then the 404 will be raised.
        """
        return self.instance.attachments.all()

    def create(self, request, *args, **kwargs):
        serializer = UploadAttachmentsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attachments = serializer.save(created_by=request.user)
        self.instance.attachments.add(*attachments)
        root_serializer_class = self.get_serializer_class()
        return response.Response(
            {'data': [root_serializer_class(a).data for a in attachments]},
            status=status.HTTP_201_CREATED
        )
