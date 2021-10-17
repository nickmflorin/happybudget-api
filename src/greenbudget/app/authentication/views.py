from ratelimit.decorators import ratelimit

from django.conf import settings
from django.contrib.auth import logout, login as django_login
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_post_parameters

from rest_framework import (
    views, response, generics, status, mixins, viewsets, permissions)
from rest_framework.permissions import AllowAny
from greenbudget.app.authentication.exceptions import AccountDisabledError

from greenbudget.lib.drf.exceptions import (
    RequiredFieldError, InvalidFieldError)
from greenbudget.app.authentication.exceptions import RateLimitedError
from greenbudget.app.user.models import User
from greenbudget.app.user.serializers import UserSerializer
from greenbudget.app.user.utils import send_forgot_password_email

from .backends import CsrfExcemptCookieSessionAuthentication
from .middleware import TokenCookieMiddleware
from .models import ResetUID
from .serializers import (
    LoginSerializer, SocialLoginSerializer, ResetPasswordSerializer,
    SendEmailVerificationSerializer, EmailVerificationSerializer,
    TokenRefreshSerializer)
from .utils import parse_token_from_request


def sensitive_post_parameters_m(*args):
    return method_decorator(sensitive_post_parameters(*args))


class TokenRefreshView(views.APIView):
    authentication_classes = (CsrfExcemptCookieSessionAuthentication, )

    def get(self, request, *args, **kwargs):
        return response.Response({
            "detail": _("Successfully refreshed token."),
        }, status=status.HTTP_200_OK)


class TokenValidateView(views.APIView):
    authentication_classes = (CsrfExcemptCookieSessionAuthentication, )

    def post(self, request, *args, **kwargs):
        token = parse_token_from_request(request)
        serializer = TokenRefreshSerializer(force_logout=True)
        user, _ = serializer.validate({"token": token})
        return response.Response({
            'user': UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)


class LogoutView(views.APIView):
    authentication_classes = []
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        logout(request)
        resp = response.Response(status=status.HTTP_201_CREATED)
        resp.delete_cookie(
            settings.JWT_TOKEN_COOKIE_NAME,
            **TokenCookieMiddleware.cookie_kwargs
        )
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

        django_login(request, user)

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


class EmailVerificationView(
        mixins.UpdateModelMixin, viewsets.GenericViewSet):
    authentication_classes = []
    permission_classes = (permissions.AllowAny, )
    serializer_class = EmailVerificationSerializer

    @sensitive_post_parameters_m('token')
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    # @ratelimit(key='user_or_ip', rate='3/s')  -> Needs to be fixed
    def create(self, request, *args, **kwargs):
        was_limited = getattr(request, 'limited', False)
        if was_limited:
            raise RateLimitedError()

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response({}, status=status.HTTP_201_CREATED)


class SendEmailVerificationView(
        mixins.UpdateModelMixin, viewsets.GenericViewSet):
    authentication_classes = []
    permission_classes = (permissions.AllowAny, )
    serializer_class = SendEmailVerificationSerializer

    # @ratelimit(key='user_or_ip', rate='3/s')  -> Needs to be fixed
    def create(self, request, *args, **kwargs):
        was_limited = getattr(request, 'limited', False)
        if was_limited:
            raise RateLimitedError()

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response({}, status=status.HTTP_201_CREATED)


class ResetPasswordView(generics.GenericAPIView):
    serializer_class = ResetPasswordSerializer
    authentication_classes = []
    permission_classes = []

    @ratelimit(key='user_or_ip', rate='3/s')
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
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
                raise AccountDisabledError(user_id=user.id)

            reset_uid = ResetUID.objects.create(user=user)
            send_forgot_password_email(user, reset_uid.token)
            return response.Response(status=status.HTTP_201_CREATED)
