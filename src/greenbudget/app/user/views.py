from ratelimit.decorators import ratelimit

from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters

from rest_framework import viewsets, mixins, response, permissions, status

from greenbudget.app.common.exceptions import RateLimitedError
from .serializers import UserSerializer, UserRegistrationSerializer


def sensitive_post_parameters_m(*args):
    return method_decorator(sensitive_post_parameters(*args))


class UserRegistrationView(mixins.CreateModelMixin, viewsets.GenericViewSet):
    authentication_classes = []
    permission_classes = (permissions.AllowAny, )
    serializer_class = UserRegistrationSerializer

    @sensitive_post_parameters_m('token_id')
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    @ratelimit(key='user_or_ip', rate='3/s')
    def create(self, request, *args, **kwargs):
        was_limited = getattr(request, 'limited', False)
        if was_limited:
            raise RateLimitedError()

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        return response.Response(
            UserSerializer(instance).data,
            status=status.HTTP_201_CREATED
        )
