from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters

from rest_framework import response, status

from happybudget.app import views, permissions, exceptions

from .filters import UserSearchFilterBackend
from .models import User
from .serializers import (
    UserSerializer, UserRegistrationSerializer, ChangePasswordSerializer,
    SimpleUserSerializer)


def sensitive_post_parameters_m(*args):
    return method_decorator(sensitive_post_parameters(*args))


class UserRegistrationView(views.CreateModelMixin, views.GenericViewSet):
    authentication_classes = []
    permission_classes = (permissions.AllowAny, )
    serializer_class = UserRegistrationSerializer

    @sensitive_post_parameters_m('password')
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        instance.send_email_verification_email()

        return response.Response(
            UserSerializer(instance).data,
            status=status.HTTP_201_CREATED
        )


class UserViewSet(views.ListModelMixin, views.GenericViewSet):
    serializer_class = SimpleUserSerializer
    search_fields = ['email', 'name']
    filter_backends = [UserSearchFilterBackend]

    def get_queryset(self):
        if 'search' not in self.request.query_params:
            raise exceptions.BadRequest("The search parameter is required.")
        return User.objects.fully_authenticated()


class ActiveUserViewSet(views.UpdateModelMixin, views.GenericViewSet):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class ChangePasswordView(ActiveUserViewSet):
    serializer_class = ChangePasswordSerializer

    @sensitive_post_parameters_m('password', 'new_password')
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data,
            instance=self.get_object(),
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return response.Response(
            UserSerializer(instance).data,
            status=status.HTTP_200_OK
        )
