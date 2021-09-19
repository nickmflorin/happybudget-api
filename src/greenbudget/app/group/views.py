from rest_framework import viewsets, mixins

from .models import Group
from .serializers import GroupSerializer


class GroupViewSet(
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """
    Viewset to handle requests to the following endpoints:

    (1) PATCH /groups/<pk>/
    (2) GET /groups/<pk>/
    (3) DELETE /groups/<pk>/
    """
    lookup_field = 'pk'
    serializer_class = GroupSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # The parent object is needed in context in order to update the children
        # of a Group - but that will only happen in a PATCH request for this
        # view (POST request is handled by another view).
        if self.detail is True:
            obj = self.get_object()
            context['parent'] = obj.parent
        return context

    def get_queryset(self):
        return Group.objects.filter(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
