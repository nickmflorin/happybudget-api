from django.contrib.auth import login
from django.core.files.storage import get_storage_class
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters

from rest_framework import (
    viewsets, mixins, response, permissions, status, decorators)

from greenbudget.app.authentication.exceptions import RateLimitedError

from .serializers import UserSerializer, UserRegistrationSerializer
from .utils import upload_temp_user_image_to


def sensitive_post_parameters_m(*args):
    return method_decorator(sensitive_post_parameters(*args))


@decorators.api_view(['POST'])
def temp_upload_user_image_view(request):
    image = request.data['image']
    storage_cls = get_storage_class()
    storage = storage_cls()
    image_name = upload_temp_user_image_to(
        user=request.user,
        filename=image.name
    )
    storage.save(image_name, image.file)
    file_url = storage.url(image_name)
    return response.Response({'fileUrl': file_url})


class UserRegistrationView(mixins.CreateModelMixin, viewsets.GenericViewSet):
    authentication_classes = []
    permission_classes = (permissions.AllowAny, )
    serializer_class = UserRegistrationSerializer

    @sensitive_post_parameters_m('password')
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    # @ratelimit(key='user_or_ip', rate='3/s')  -> Needs to be fixed
    def create(self, request, *args, **kwargs):
        was_limited = getattr(request, 'limited', False)
        if was_limited:
            raise RateLimitedError()

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        login(request, instance,
            backend='django.contrib.auth.backends.ModelBackend')

        resp = response.Response(
            UserSerializer(instance).data,
            status=status.HTTP_201_CREATED
        )
        instance.is_first_time = False
        instance.save()
        return resp


class ActiveUserViewSet(mixins.UpdateModelMixin, viewsets.GenericViewSet):
    lookup_field = 'pk'
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
