import os

from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters

from rest_framework import (
    viewsets, mixins, response, permissions, status, decorators)

from greenbudget.app.common.exceptions import RateLimitedError

from .serializers import UserSerializer, UserRegistrationSerializer
from .storages import TempUserImageStorage


def sensitive_post_parameters_m(*args):
    return method_decorator(sensitive_post_parameters(*args))


@decorators.api_view(['PUT', 'POST', 'GET', 'PATCH'])
def temp_upload_user_image_view(request):
    image = request.data['image']

    directory = 'temp/%s' % request.user.email
    path = os.path.join(directory, image.name)

    media_storage = TempUserImageStorage()
    if not media_storage.exists(path):
        media_storage.save(path, image.file)
        file_url = media_storage.url(path)
        return response.Response({
            'fileUrl': file_url,
        })
    else:
        # TODO: Since this is a temporary image upload for purposes of
        # displaying the image so it can be cropped/viewed before saving,
        # we probably don't want it to fail if it is a duplicate but instead
        # generate a unique name.
        return response.Response({
            'message': (
                "Error: file {filename} already exists at "
                "{directory} in bucket {bucket_name}".format(
                    filename=image.name,
                    directory=directory,
                    bucket_name=media_storage.bucket_name
                )
            )}, status=400)


class UserRegistrationView(mixins.CreateModelMixin, viewsets.GenericViewSet):
    authentication_classes = []
    permission_classes = (permissions.AllowAny, )
    serializer_class = UserRegistrationSerializer

    @ sensitive_post_parameters_m('password')
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

        return response.Response(
            UserSerializer(instance).data,
            status=status.HTTP_201_CREATED
        )
