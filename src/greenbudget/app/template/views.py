from happybudget.app import views, permissions
from happybudget.app.budget.cache import budget_instance_cache

from .models import Template
from .serializers import TemplateSerializer, TemplateSimpleSerializer


class TemplateCommunityViewSet(
    views.CreateModelMixin,
    views.ListModelMixin,
    views.GenericViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /templates/community/
    (2) POST /templates/community/
    """
    permission_classes = (permissions.IsStaffUserOrReadOnly, )
    serializer_class = TemplateSerializer
    ordering_fields = ['updated_at', 'name', 'created_at']
    search_fields = ['name']

    def get_serializer_class(self):
        if self.action == 'list':
            return TemplateSimpleSerializer
        return TemplateSerializer

    def create_kwargs(self, serializer):
        return {**super().create_kwargs(serializer), **{'community': True}}

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(community=True)
        return context

    def get_queryset(self):
        qs = Template.objects.community()
        if not self.request.user.is_staff:
            return qs.filter(hidden=False)
        return qs


@budget_instance_cache
class TemplateViewSet(
    views.CreateModelMixin,
    views.ListModelMixin,
    views.GenericViewSet
):
    """
    ViewSet to handle requests to the following endpoints:

    (1) GET /templates/
    (2) POST /templates/
    """
    serializer_class = TemplateSerializer
    ordering_fields = ['updated_at', 'name', 'created_at']
    search_fields = ['name']

    def get_serializer_class(self):
        if self.action == 'list':
            return TemplateSimpleSerializer
        return TemplateSerializer

    def get_queryset(self):
        qs = Template.objects.all()
        if self.action in ('list', 'create'):
            return qs.user(self.request.user)
        return qs
