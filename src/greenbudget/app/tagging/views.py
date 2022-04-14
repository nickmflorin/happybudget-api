from rest_framework import viewsets

from greenbudget.app import permissions, views

from .models import Color
from .serializers import ColorSerializer


def ColorsViewSet(model_cls, permission_classes=None):
    """
    Viewset to handle requests to the following endpoints:

    (1) GET /<entity>/colors/
    """
    pms = permission_classes or permissions.OR(
        permissions.IsFullyAuthenticated,
        permissions.IsPublic
    )

    class _ColorsViewSet(views.ListModelMixin, viewsets.GenericViewSet):
        serializer_class = ColorSerializer
        permission_classes = [pms]

        def get_queryset(self):
            return Color.objects.for_model(model_cls).all()
    return _ColorsViewSet
