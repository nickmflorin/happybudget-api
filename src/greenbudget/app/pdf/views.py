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

    (1) GET /pdf/header-templates/
    (2) POST /pdf/header-templates/
    (3) GET /pdf/header-templates/<pk>/
    (4) PATCH /pdf/header-templates/<pk>/
    (5) DELETE /pdf/header-templates/<pk>/
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
