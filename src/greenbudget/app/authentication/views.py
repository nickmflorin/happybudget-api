from ratelimit.decorators import ratelimit

from django.conf import settings
from django.contrib.auth import logout, login as django_login
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters

from rest_framework import views, response, generics, status
from rest_framework.permissions import AllowAny
from greenbudget.app.authentication.exceptions import AccountDisabledError

from greenbudget.lib.rest_framework_utils.exceptions import (
    RequiredFieldError, InvalidFieldError)
from greenbudget.app.common.exceptions import RateLimitedError
from greenbudget.app.user.models import User
from greenbudget.app.user.serializers import UserSerializer
from greenbudget.app.user.utils import send_forgot_password_email

from .models import ResetUID
from .serializers import (
    LoginSerializer, SocialLoginSerializer, ResetPasswordSerializer)


def sensitive_post_parameters_m(*args):
    return method_decorator(sensitive_post_parameters(*args))


class LogoutView(views.APIView):
    authentication_classes = []
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        logout(request)
        resp = response.Response(status=status.HTTP_201_CREATED)
        resp.delete_cookie(settings.JWT_TOKEN_COOKIE_NAME)
        return resp


class AbstractLoginView(generics.GenericAPIView):
    authentication_classes = []
    permission_classes = (AllowAny, )

    # @ratelimit(key='user_or_ip', rate='3/s')  -> Needs to be fixed
    def post(self, request, *args, **kwargs):
        was_limited = getattr(request, 'limited', False)
        if was_limited:
            raise RateLimitedError()

        serializer = self.get_serializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        django_login(
            request, user, backend='django.contrib.auth.backends.ModelBackend')

        resp = response.Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED
        )
        if user.is_first_time is True:
            user.is_first_time = False
            user.save()
        return resp


class SocialLoginView(AbstractLoginView):
    serializer_class = SocialLoginSerializer

    @sensitive_post_parameters_m('token_id')
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class LoginView(AbstractLoginView):
    serializer_class = LoginSerializer

    @sensitive_post_parameters_m('password')
    def dispatch(self, request, *args, **kwargs):
        return super(LoginView, self).dispatch(request, *args, **kwargs)


class ResetPasswordView(generics.GenericAPIView):
    serializer_class = ResetPasswordSerializer
    authentication_classes = []
    permission_classes = []

    @ratelimit(key='user_or_ip', rate='3/s')
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        user.set_password(serializer.validated_data["password"])
        user.save()
        return response.Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED
        )


class ForgotPasswordView(generics.GenericAPIView):
    authentication_classes = []
    permission_classes = []

    @ratelimit(key='user_or_ip', rate='3/s')
    def post(self, request, *args, **kwargs):
        if 'email' not in request.data:
            raise RequiredFieldError('email')
        try:
            user = User.objects.get(email=request.data["email"])
        except User.DoesNotExist:
            raise InvalidFieldError('email',
                message=("There is not a user associated with the provided "
                    "email.")
            )
        else:
            if not user.is_active:
                raise AccountDisabledError()

            reset_uid = ResetUID.objects.create(user=user)
            send_forgot_password_email(user, reset_uid.token)
            return response.Response(status=status.HTTP_201_CREATED)
