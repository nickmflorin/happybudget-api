from rest_framework import viewsets, mixins

from .serializers import ContactSerializer


class ContactViewSet(
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
    serializer_class = ContactSerializer
    ordering_fields = ['updated_at', 'first_name', 'last_name', 'created_at']
    search_fields = ['first_name', 'last_name', 'role', 'location']

    def get_queryset(self):
        # TODO: Make sure this will not work for inactive users.
        return self.request.user.contacts.all()
