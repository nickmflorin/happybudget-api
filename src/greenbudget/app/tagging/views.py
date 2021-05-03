from rest_framework import mixins, viewsets

from .models import Color
from .serializers import ColorSerializer


def ColorsViewSet(model_cls):
    """
    Viewset to handle requests to the following endpoints:

    (1) GET /<entity>/colors/
    """
    class _ColorsViewSet(
        mixins.ListModelMixin,
        viewsets.GenericViewSet
    ):
        serializer_class = ColorSerializer

        def get_queryset(self):
            return Color.objects.for_model(model_cls).all()
    return _ColorsViewSet
