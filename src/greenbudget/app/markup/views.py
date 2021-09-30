from django.utils.functional import cached_property
from rest_framework import viewsets, mixins, decorators, response, status

from .models import Markup
from .serializers import (
    MarkupSerializer,
    MarkupAddChildrenSerializer,
    MarkupRemoveChildrenSerializer
)


class MarkupViewSet(
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """
    Viewset to handle requests to the following endpoints:

    (1) PATCH /markups/<pk>/
    (2) GET /markups/<pk>/
    (3) DELETE /markups/<pk>/
    """
    lookup_field = 'pk'
    serializer_class = MarkupSerializer

    def get_serializer_context(self, parent=None):
        context = super().get_serializer_context()
        # The parent object is needed in context in order to update the children
        # of a Markup - but that will only happen in a PATCH request for this
        # view (POST request is handled by another view).
        if self.detail is True and parent is None:
            obj = self.get_object()
            context['parent'] = obj.parent
        if parent is not None:
            # The parent must be explicitly provided in some cases where the
            # Markup instance may be deleted due to a lack of children.
            context['parent'] = parent
        return context

    @cached_property
    def instance_cls(self):
        instance = self.get_object()
        return type(instance)

    def get_queryset(self):
        return Markup.objects.filter(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @decorators.action(methods=["PATCH"], detail=True,
        url_path='remove-children')
    def remove_children(self, request, *args, **kwargs):
        instance = self.get_object()

        # We have to temporarily store the original values for these properties
        # because when removing a Markup's children, the Markup may be deleted
        # if it does not have anymore children after the designated children are
        # removed.
        original_pk = instance.pk
        original_parent = instance.parent

        serializer = MarkupRemoveChildrenSerializer(
            instance=instance,
            data=request.data,
            partial=True,
            context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        serializer_cls = self.get_serializer_class()
        data = serializer_cls(
            instance=instance,
            context=self.get_serializer_context(parent=original_parent)
        ).data

        # If the instance was deleted because it had no more children, we do
        # not want to return an instance with a null ID in the response - so
        # we must modify the response in this case.
        if instance.id is None:
            data['data']['id'] = original_pk

        return response.Response(data, status=status.HTTP_200_OK)

    @decorators.action(methods=["PATCH"], detail=True,
        url_path='add-children')
    def add_children(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = MarkupAddChildrenSerializer(
            instance=instance,
            data=request.data,
            partial=True,
            context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        serializer_cls = self.get_serializer_class()
        data = serializer_cls(
            instance=instance,
            context=self.get_serializer_context()
        ).data

        return response.Response(data, status=status.HTTP_200_OK)
