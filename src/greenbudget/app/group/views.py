from django.utils.functional import cached_property
from rest_framework import viewsets, mixins

from greenbudget.app.tagging.models import Color
from greenbudget.app.tagging.serializers import ColorSerializer

from .models import (
    Group,
    BudgetAccountGroup,
    TemplateAccountGroup,
    BudgetSubAccountGroup,
    TemplateSubAccountGroup
)
from .serializers import (
    BudgetAccountGroupSerializer,
    BudgetSubAccountGroupSerializer,
    TemplateAccountGroupSerializer,
    TemplateSubAccountGroupSerializer
)


class GroupColorsViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """
    Viewset to handle requests to the following endpoints:

    (1) GET /groups/colors/
    """
    serializer_class = ColorSerializer

    def get_queryset(self):
        return Color.objects.for_model(Group).all()


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

    @cached_property
    def instance_cls(self):
        instance = self.get_object()
        return type(instance)

    def get_serializer_class(self):
        mapping = {
            BudgetAccountGroup: BudgetAccountGroupSerializer,
            TemplateAccountGroup: TemplateAccountGroupSerializer,
            BudgetSubAccountGroup: BudgetSubAccountGroupSerializer,
            TemplateSubAccountGroup: TemplateSubAccountGroupSerializer
        }
        return mapping[self.instance_cls]

    def get_queryset(self):
        return Group.objects.filter(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
