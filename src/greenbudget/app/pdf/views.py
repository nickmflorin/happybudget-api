from rest_framework import viewsets, mixins

from .models import HeaderTemplate
from .serializers import (
    HeaderTemplateSerializer, SimpleHeaderTemplateSerializer)


class HeaderTemplateViewSet(
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /contacts/
    (2) POST /contacts/
    (3) GET /contacts/<pk>/
    (4) PATCH /contacts/<pk>/
    (5) DELETE /contacts/<pk>/
    """
    lookup_field = 'pk'
    serializer_class = HeaderTemplateSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return SimpleHeaderTemplateSerializer
        return self.serializer_class

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            request=self.request,
            user=self.request.user
        )
        return context

    def get_queryset(self):
        return HeaderTemplate.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
