from django.db import models
from rest_framework import decorators, response, status, filters

from greenbudget.lib.drf.bulk_serializers import (
    create_bulk_create_serializer,
    create_bulk_update_serializer,
    create_bulk_delete_serializer
)

from greenbudget.app import views, mixins
from greenbudget.app.actual.serializers import TaggedActualSerializer
from greenbudget.app.io.views import GenericAttachmentViewSet

from .cache import user_contacts_cache
from .filters import ContactSearchFilterBackend
from .mixins import ContactNestedMixin
from .models import Contact
from .serializers import ContactSerializer, ContactDetailSerializer


class ContactAttachmentViewSet(
    ContactNestedMixin,
    GenericAttachmentViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /contacts/<pk>/attachments/
    (2) DELETE /contacts/<pk>/attachments/pk/
    (3) POST /contacts/<pk>/attachments/
    """


class ContactTaggedActualsViewSet(
    mixins.ListModelMixin,
    ContactNestedMixin,
    views.GenericViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /contacts/<pk>/tagged-actuals/
    """
    serializer_class = TaggedActualSerializer

    def get_queryset(self):
        return self.instance.tagged_actuals.order_by('date')


@user_contacts_cache
class ContactViewSet(
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    views.GenericViewSet
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
    ordering_fields = []
    search_fields = ['label', 'name']
    serializer_class = ContactSerializer
    serializer_classes = (
        (lambda view: view.action in ('partial_update', 'create', 'retrieve'),
            ContactDetailSerializer),
    )
    filter_backends = [
        ContactSearchFilterBackend,
        filters.OrderingFilter
    ]

    def get_queryset(self):
        return self.request.user.created_contacts.all()

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
            serializer_cls=self.serializer_class,
            filter_qs=models.Q(created_by=request.user)
        )
        serializer = serializer_cls(data=request.data)
        serializer.is_valid(raise_exception=True)
        children = self.perform_update(serializer)
        return response.Response({
            'children': self.serializer_class(children, many=True).data
        }, status=status.HTTP_200_OK)

    @decorators.action(detail=False, url_path="bulk-create", methods=["PATCH"])
    def bulk_create(self, request, *args, **kwargs):
        serializer_cls = create_bulk_create_serializer(
            serializer_cls=self.serializer_class,
        )
        serializer = serializer_cls(data=request.data)
        serializer.is_valid(raise_exception=True)

        # The serializer here is a bulk create serializer, which does not have
        # a reference to the Contact model because it is not a ModelSerializer.
        # This means that we have to explicitly include the create_kwargs that
        # would have otherwise been automatically generated.
        children = self.perform_create(
            serializer,
            created_by=self.request.user,
            updated_by=self.request.user
        )
        return response.Response({
            'children': self.serializer_class(children, many=True).data
        }, status=status.HTTP_201_CREATED)
