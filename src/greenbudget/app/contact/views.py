from django.db import models
from rest_framework import viewsets, mixins, decorators, response, status

from greenbudget.lib.drf.bulk_serializers import (
    create_bulk_create_serializer,
    create_bulk_update_serializer,
    create_bulk_delete_serializer
)

from greenbudget.app.views import GenericViewSet
from greenbudget.app.io.serializers import (
    AttachmentSerializer, UploadAttachmentSerializer)

from .cache import user_contacts_cache
from .mixins import ContactNestedMixin
from .models import Contact
from .serializers import ContactSerializer


class ContactAttachmentViewSet(
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    mixins.CreateModelMixin,
    ContactNestedMixin,
    viewsets.GenericViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /contacts/<pk>/attachments/
    (2) DELETE /contacts/<pk>/attachments/pk/
    (3) POST /contacts/<pk>/attachments/
    """
    contact_lookup_field = ("pk", "contact_pk")
    serializer_class = AttachmentSerializer
    lookup_field = "pk"

    def get_queryset(self):
        return self.contact.attachments.all()

    def create(self, request, *args, **kwargs):
        serializer = UploadAttachmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attachment = serializer.save(created_by=request.user)
        self.contact.attachments.add(attachment)
        root_serializer_class = self.get_serializer_class()
        return response.Response(
            root_serializer_class(instance=attachment).data,
            status=status.HTTP_200_OK
        )


@user_contacts_cache(get_instance_from_view=lambda view: view.request.user.pk)
class ContactViewSet(
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /contacts/
    (2) POST /contacts/
    (3) GET /contacts/<pk>/
    (4) PATCH /contacts/<pk>/
    (5) DELETE /contacts/<pk>/
    (6) PATCH /contacts/bulk-delete/
    (7) PATCH /contacts/bulk-update/
    (8) PATCH /contacts/bulk-create/
    """
    lookup_field = 'pk'
    serializer_class = ContactSerializer
    ordering_fields = ['updated_at', 'first_name', 'last_name', 'created_at']
    search_fields = ['first_name', 'last_name']

    def get_queryset(self):
        return self.request.user.created_contacts.all()

    def perform_create(self, serializer):
        return serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )

    def perform_update(self, serializer):
        return serializer.save(updated_by=self.request.user)

    @decorators.action(detail=False, url_path="bulk-delete", methods=["PATCH"])
    def bulk_delete(self, request, *args, **kwargs):
        serializer_cls = create_bulk_delete_serializer(
            filter_qs=models.Q(created_by=request.user),
            child_cls=Contact
        )
        serializer = serializer_cls(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    @decorators.action(detail=False, url_path="bulk-update", methods=["PATCH"])
    def bulk_update(self, request, *args, **kwargs):
        serializer_cls = create_bulk_update_serializer(
            serializer_cls=ContactSerializer,
            filter_qs=models.Q(created_by=request.user)
        )
        serializer = serializer_cls(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return response.Response(status=status.HTTP_200_OK)

    @decorators.action(detail=False, url_path="bulk-create", methods=["PATCH"])
    def bulk_create(self, request, *args, **kwargs):
        serializer_cls = create_bulk_create_serializer(
            serializer_cls=ContactSerializer,
        )
        serializer = serializer_cls(data=request.data)
        serializer.is_valid(raise_exception=True)
        children = self.perform_create(serializer)

        return response.Response({
            'data': self.serializer_class(children, many=True).data
        }, status=status.HTTP_201_CREATED)
