from happybudget.app import views

from .models import HeaderTemplate
from .serializers import (
    HeaderTemplateSerializer, SimpleHeaderTemplateSerializer)


class HeaderTemplateViewSet(
    views.UpdateModelMixin,
    views.RetrieveModelMixin,
    views.CreateModelMixin,
    views.DestroyModelMixin,
    views.ListModelMixin,
    views.GenericViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /pdf/header-templates/
    (2) POST /pdf/header-templates/
    (3) GET /pdf/header-templates/<pk>/
    (4) PATCH /pdf/header-templates/<pk>/
    (5) DELETE /pdf/header-templates/<pk>/
    """
    serializer_class = HeaderTemplateSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return SimpleHeaderTemplateSerializer
        return self.serializer_class

    def get_queryset(self):
        return HeaderTemplate.objects.filter(created_by=self.request.user)
